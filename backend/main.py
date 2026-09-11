import sys
import os

# Ensure backend directory is in sys.path for direct imports (e.g. database, models)
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

app = FastAPI(title="PetrolQ API", description="Oil & Gas Drilling Data API", lifespan=lifespan)

# Configure CORS - allow the Netlify frontend URL in production
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
cors_origins = ["*"] if FRONTEND_URL == "*" else [FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount offline tiles
tiles_dir = os.path.join(backend_dir, "static", "tiles")
os.makedirs(tiles_dir, exist_ok=True)
app.mount("/tiles", StaticFiles(directory=tiles_dir), name="tiles")

app.include_router(upload_router)
app.include_router(correlate_router)
app.include_router(lookahead_router)
app.include_router(ppfg_router)
app.include_router(dossier_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "PetrolQ API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

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
    
    tvd_max = float(well.total_depth_tvd or 3500.0)
    db_events = db.query(SyntheticEvent).filter(
        SyntheticEvent.well_id == well_id,
        SyntheticEvent.formation.isnot(None)
    ).all()
    return compute_realistic_trajectory(str(well_id), tvd_max, is_active=is_active, db_events=db_events)

@app.get("/api/wells/{well_id}/anti-collision")
def get_anti_collision(
    well_id: str, 
    offset_ids: Optional[str] = Query(None, description="Comma-separated offset well IDs"),
    db: Session = Depends(get_db)
):
    active_well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not active_well:
        raise HTTPException(status_code=404, detail="Active well not found")
        
    active_traj = compute_realistic_trajectory(str(well_id), float(active_well.total_depth_tvd or 3500.0), is_active=True)
    
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
        off_traj = compute_realistic_trajectory(str(off.well_id), float(off.total_depth_tvd or 3500.0), is_active=False)
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
        embedding_val = getattr(event, "embedding", None)
        if embedding_val is None or len(embedding_val) == 0:
            continue
            
        # Calculate cosine similarity in-memory
        # (Since pgvector extension compilation failed, we use numpy on standard Postgres Arrays)
        sim = compute_cosine_similarity(query_embedding, embedding_val)
        
        results.append(
            RAGSearchResponse(
                similarity_score=float(sim),
                well_id=str(event.well_id),
                # Fallback to start depth if singular depth_tvd is required
                depth_tvd=float(event.depth_start_tvd) if event.depth_start_tvd is not None else 0.0,
                event_type=str(event.event_type or ""),
                root_cause=str(event.root_cause or ""),
                mitigation_applied=str(event.mitigation_applied or "")
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
    
    if ml_service is None:
        ml_service = HazardPredictionService()
        
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

from simulator import ws_manager, telemetry_simulator

class ScenarioRequest(BaseModel):
    scenario: str  # "gas_kick", "lost_circulation", "stuck_pipe", "normal"

class ControlRequest(BaseModel):
    action: str  # "play", "pause", "reset", "step", "speed", "seek"
    well_id: Optional[str] = None
    depth: Optional[float] = None
    speed_multiplier: Optional[float] = None

@app.post("/api/simulator/scenario")
async def trigger_scenario(req: ScenarioRequest):
    """
    CORRECTION 4 REQUIREMENT:
    Modifies underlying simulated telemetry values realistically for that scenario type.
    Computes resulting risk scores from those simulated values and broadcasts to all WebSocket clients.
    """
    res = telemetry_simulator.set_scenario(req.scenario)
    await ws_manager.broadcast({
        "status": "success",
        "data": res["data"],
        "prediction": res["prediction"],
        "scenario": res["scenario"],
        "is_running": telemetry_simulator.is_running
    })
    return {
        "status": "success",
        "scenario": res["scenario"],
        "data": res["data"],
        "prediction": res["prediction"]
    }

@app.post("/api/simulator/control")
async def control_simulator(req: ControlRequest):
    """
    Controls in-app telemetry playback: play, pause, reset, or step.
    """
    if req.action == "play":
        telemetry_simulator.start()
    elif req.action == "pause":
        telemetry_simulator.pause()
    elif req.action == "reset":
        depth_val = float(req.depth) if req.depth is not None else 2240.0
        telemetry_simulator.reset(well_id=req.well_id or "OIL-BAGHJAN-1", depth_tvd=depth_val)
        await telemetry_simulator.step_and_broadcast()
    elif req.action == "set_well":
        depth_val = float(req.depth) if req.depth is not None else 2240.0
        telemetry_simulator.reset(well_id=req.well_id or "OIL-BAGHJAN-1", depth_tvd=depth_val)
        await telemetry_simulator.step_and_broadcast()
    elif req.action == "step":
        await telemetry_simulator.step_and_broadcast()
    elif req.action == "speed" and req.speed_multiplier is not None:
        telemetry_simulator.speed_multiplier = req.speed_multiplier
    elif req.action == "seek" and req.depth is not None:
        await telemetry_simulator.seek(req.depth)
    return telemetry_simulator.get_status()

@app.get("/api/simulator/status")
def get_simulator_status():
    """Returns current telemetry simulator state."""
    return telemetry_simulator.get_status()

@app.websocket("/api/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    Centralized multi-client WebSocket telemetry endpoint.
    All connected browser clients receive synchronized live streaming updates.
    """
    await ws_manager.connect(websocket)
    global ml_service
    
    # Send current state immediately on connect
    current_status = telemetry_simulator.get_status()
    current_params = current_status["current_params"]
    prediction = ml_service.predict_risk(current_params) if ml_service else {}
    
    try:
        await websocket.send_json({
            "status": "success",
            "data": current_params,
            "prediction": prediction,
            "scenario": current_status["active_scenario"],
            "is_running": current_status["is_running"]
        })
    except Exception:
        pass
        
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
                    
                    # Centralized broadcast to ALL connected client tabs
                    await ws_manager.broadcast({
                        "status": "success",
                        "data": params,
                        "prediction": prediction,
                        "scenario": telemetry_simulator.active_scenario,
                        "is_running": telemetry_simulator.is_running
                    })
                else:
                    await websocket.send_json({"status": "error", "message": "ML service unavailable"})
            except json.JSONDecodeError:
                await websocket.send_json({"status": "error", "message": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

