import sys
import os

# Ensure backend directory is in sys.path for direct imports (e.g. database, models)
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import cast
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from geoalchemy2.types import Geography
from typing import List, Optional
import numpy as np
from pydantic import BaseModel

from contextlib import asynccontextmanager

from database import get_db
from models import WellMaster, SyntheticEvent, WellLog
from schemas import WellResponse, EventResponse, WellLogResponse, TelemetryInput, RiskPredictionResponse
from nlp.config import get_embedding
from ml.service import HazardPredictionService
from api.upload import router as upload_router
from api.correlate import router as correlate_router
from api.lookahead import router as lookahead_router
from api.ppfg import router as ppfg_router
from api.dossier import router as dossier_router

class RAGSearchResponse(BaseModel):
    similarity_score: float
    well_id: str
    depth_tvd: float
    event_type: str
    root_cause: str
    mitigation_applied: str

def compute_cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# Initialize the ML service globally
ml_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_service
    # Instantiate service on startup to load models into memory
    ml_service = HazardPredictionService()
    yield
    # Clean up on shutdown if necessary

app = FastAPI(title="eRTMAC-NWIS API", description="Oil & Gas Drilling Data API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(correlate_router)
app.include_router(lookahead_router)
app.include_router(ppfg_router)
app.include_router(dossier_router)

@app.get("/api/wells/nearby", response_model=List[WellResponse])
def get_nearby_wells(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Radius in kilometers"),
    db: Session = Depends(get_db)
):
    """
    Search for wells within a specified radius (in km) using PostGIS spatial queries.
    """
    # PostGIS geography calculations use meters
    radius_meters = radius_km * 1000.0

    # Build the target point (SRID 4326)
    target_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    # Use ST_DWithin cast to Geography for highly accurate meter-based spatial distance calculation
    wells = db.query(WellMaster).filter(
        ST_DWithin(
            cast(WellMaster.surface_location, Geography),
            cast(target_point, Geography),
            radius_meters
        )
    ).all()

    return wells

@app.get("/api/wells/{well_id}/history")
def get_well_history(
    well_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the event history and well logs for a specific well.
    """
    # Verify the well exists first
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    # Fetch events and logs
    events = db.query(SyntheticEvent).filter(SyntheticEvent.well_id == well_id).all()
    logs = db.query(WellLog).filter(WellLog.well_id == well_id).all()

    # Serialize using Pydantic
    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "logs": [WellLogResponse.model_validate(l) for l in logs]
    }

import hashlib

from trajectory_calc import compute_realistic_trajectory, compute_anti_collision

@app.get("/api/wells/{well_id}/trajectory")
def get_well_trajectory(well_id: str, is_active: bool = Query(False), db: Session = Depends(get_db)):
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    tvd_max = well.total_depth_tvd or 3500.0
    db_events = db.query(SyntheticEvent).filter(
        SyntheticEvent.well_id == well_id,
        SyntheticEvent.formation.isnot(None)
    ).all()
    return compute_realistic_trajectory(well_id, tvd_max, is_active=is_active, db_events=db_events)

@app.get("/api/wells/{well_id}/anti-collision")
def get_anti_collision(
    well_id: str, 
    offset_ids: Optional[str] = Query(None, description="Comma-separated offset well IDs"),
    db: Session = Depends(get_db)
):
    active_well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not active_well:
        raise HTTPException(status_code=404, detail="Active well not found")
        
    active_traj = compute_realistic_trajectory(well_id, active_well.total_depth_tvd or 3500.0, is_active=True)
    
    if offset_ids:
        offset_list = [oid.strip() for oid in offset_ids.split(",") if oid.strip()]
        offsets = db.query(WellMaster).filter(WellMaster.well_id.in_(offset_list)).all()
    else:
        offsets = db.query(WellMaster).filter(WellMaster.well_id != well_id).all()
        
    results = []
    closest_overall = None
    min_dist_overall = float("inf")
    
    for off in offsets:
        if off.well_id == well_id:
            continue
        off_traj = compute_realistic_trajectory(off.well_id, off.total_depth_tvd or 3500.0, is_active=False)
        ac = compute_anti_collision(active_traj, off_traj)
        results.append(ac)
        
        if ac["min_distance_m"] < min_dist_overall:
            min_dist_overall = ac["min_distance_m"]
            closest_overall = ac
            
    return {
        "active_well_id": well_id,
        "closest_approach": closest_overall,
        "offset_evaluations": results
    }

@app.get("/api/events/search", response_model=List[RAGSearchResponse])
def search_events(
    query: str,
    formation: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Semantic RAG search endpoint.
    Finds historical drilling incidents matching the natural language query.
    """
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # Base query for events
    db_query = db.query(SyntheticEvent)
    
    # Optional relational filter
    if formation:
        db_query = db_query.filter(SyntheticEvent.formation.ilike(f"%{formation}%"))
        
    events = db_query.all()
    
    results = []
    for event in events:
        if not event.embedding or len(event.embedding) == 0:
            continue
            
        # Calculate cosine similarity in-memory
        # (Since pgvector extension compilation failed, we use numpy on standard Postgres Arrays)
        sim = compute_cosine_similarity(query_embedding, event.embedding)
        
        results.append(
            RAGSearchResponse(
                similarity_score=sim,
                well_id=event.well_id,
                # Fallback to start depth if singular depth_tvd is required
                depth_tvd=event.depth_start_tvd if event.depth_start_tvd is not None else 0.0,
                event_type=event.event_type,
                root_cause=event.root_cause,
                mitigation_applied=event.mitigation_applied
            )
        )
        
    # Sort descending by similarity
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return results[:limit]

@app.post("/api/predict-risk", response_model=RiskPredictionResponse)
def predict_risk(telemetry: TelemetryInput):
    """
    Real-time ML inference endpoint for drilling hazard prediction.
    Accepts incoming sensor telemetry and returns a risk probability, risk level, 
    and top contributing factors via SHAP.
    """
    global ml_service
    
    if not ml_service:
        raise HTTPException(status_code=503, detail="ML Service is not initialized.")
        
    try:
        # Convert schema to dict
        params = telemetry.model_dump()
        
        # Run prediction
        prediction = ml_service.predict_risk(params)
        
        if "error" in prediction:
            raise HTTPException(status_code=500, detail=prediction["error"])
            
        return prediction
    except ValueError as e:
        # Handle out-of-bounds or formatting errors natively gracefully
        raise HTTPException(status_code=400, detail=f"Invalid telemetry data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.websocket("/api/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    global ml_service
    print("Client connected to telemetry WebSocket.")
    try:
        import json
        while True:
            data = await websocket.receive_text()
            try:
                params = json.loads(data)
                
                # Run prediction
                if ml_service:
                    from fastapi.concurrency import run_in_threadpool
                    prediction = await run_in_threadpool(ml_service.predict_risk, params)
                    
                    # Send back the prediction result
                    await websocket.send_json({
                        "status": "success",
                        "data": params,
                        "prediction": prediction
                    })
                else:
                    await websocket.send_json({"status": "error", "message": "ML service unavailable"})
            except json.JSONDecodeError:
                await websocket.send_json({"status": "error", "message": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
    except WebSocketDisconnect:
        print("Client disconnected from telemetry WebSocket.")
