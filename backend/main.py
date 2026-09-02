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

def compute_realistic_trajectory(well_id: str, tvd_max: float, is_active: bool = False, db_events: list = None):
    """
    Computes a realistic 3D directional borehole trajectory.
    Uses deterministic pseudo-random seed from well_id so each well has a unique,
    consistent azimuth, build-up rate, and KOP, but fans out realistically.
    """
    seed = int(hashlib.md5(well_id.encode('utf-8')).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)
    
    # Surface wellhead position (Z=0)
    if is_active:
        x0, y0 = 0.0, 0.0
        kop = float(rng.uniform(420.0, 620.0))
        max_drift = float(rng.uniform(300.0, 500.0))
        azimuth_deg = float(rng.uniform(35.0, 75.0)) # Active rig drifts NE
    else:
        # Offsets are placed in realistic pad/cluster positions around active rig (160m - 520m)
        surface_dist = float(rng.uniform(160.0, 520.0))
        surface_az = float(rng.uniform(0.0, 2.0 * np.pi))
        x0 = surface_dist * np.sin(surface_az)
        y0 = surface_dist * np.cos(surface_az)
        kop = float(rng.uniform(320.0, 780.0))
        max_drift = float(rng.uniform(200.0, 620.0))
        azimuth_deg = float(rng.uniform(0.0, 360.0)) # Offsets fan out across all 360 degrees
        
    azimuth_rad = np.radians(azimuth_deg)
    drift_power = float(rng.uniform(1.15, 1.55))
    turn_rate = float(rng.uniform(-12.0, 12.0))
    
    num_points = 100
    depths_z = np.linspace(0, tvd_max, num_points)
    xs = np.full_like(depths_z, x0)
    ys = np.full_like(depths_z, y0)
    
    for i, z in enumerate(depths_z):
        if z > kop:
            prog = (z - kop) / max(1.0, (tvd_max - kop))
            # S-curve build and hold profile with individual curvature power
            drift = max_drift * (np.sin(prog * np.pi / 2.0) ** drift_power)
            # Subtle realistic azimuth walk / dogleg
            az_cur = azimuth_rad + np.radians(turn_rate * np.sin(prog * np.pi))
            xs[i] = x0 + drift * np.sin(az_cur)
            ys[i] = y0 + drift * np.cos(az_cur)
            
    # Differential steps along trajectory
    dx = np.diff(xs, prepend=xs[0])
    dy = np.diff(ys, prepend=ys[0])
    dz = np.diff(depths_z, prepend=depths_z[0])
    step_md = np.sqrt(dx**2 + dy**2 + dz**2)
    md = np.cumsum(step_md)
    
    # Inclination: angle from vertical (degrees)
    inc = np.degrees(np.arctan2(np.sqrt(dx**2 + dy**2), dz + 1e-6))
    
    # Azimuth: direction from North (degrees)
    az = (np.degrees(np.arctan2(dx, dy + 1e-6)) + 360.0) % 360.0
    
    # Depth-indexed risk score (0.0 to 1.0) along trajectory
    risk_scores = []
    for z in depths_z:
        if z < 1400: # Shallow Tipam: Low risk
            r = 0.12 + 0.08 * np.sin(z / 200.0)
        elif z < 2100: # Upper Barail transition: Moderate risk
            r = 0.35 + 0.15 * np.sin(z / 150.0)
        elif z < 2750: # Known Barail kick & loss overpressure zone: High/Critical risk
            peak_factor = np.exp(-((z - 2480.0) / 200.0) ** 2)
            r = 0.55 + 0.38 * peak_factor
        else: # Deep Kopili: Elevated pressure
            r = 0.42 + 0.12 * np.sin(z / 180.0)
        risk_scores.append(round(float(np.clip(r, 0.05, 0.98)), 3))
        
    # Formation tops for this well (Assam shelf basin)
    formation_specs = [
        ("Tipam Sandstone", min(tvd_max * 0.42, 1450.0), "#EAB308", "Freshwater permeable sand reservoir"),
        ("Barail Formation", min(tvd_max * 0.68, 2400.0), "#F97316", "Overpressured sand-shale (Known Kick Zone)"),
        ("Kopili Formation", min(tvd_max * 0.85, 2950.0), "#A855F7", "Deep marine shale transition")
    ]
    
    # Check if we have specific events with formation depths
    if db_events:
        for ev in db_events:
            if ev.formation and ev.depth_start_tvd and ev.depth_start_tvd < tvd_max:
                fname = f"{ev.formation} Top"
                fcolor = "#EF4444" if "kick" in (ev.event_type or "").lower() else "#38BDF8"
                fdesc = f"Historical {ev.event_type} at {round(ev.depth_start_tvd, 1)}m"
                formation_specs.append((fname, ev.depth_start_tvd, fcolor, fdesc))
                
    formation_tops = []
    seen_depths = set()
    for name, target_tvd, color, desc in formation_specs:
        if target_tvd < tvd_max:
            idx = int(np.argmin(np.abs(depths_z - target_tvd)))
            tvd_val = round(float(depths_z[idx]), 1)
            if tvd_val in seen_depths:
                continue
            seen_depths.add(tvd_val)
            formation_tops.append({
                "name": name,
                "tvd": tvd_val,
                "md": round(float(md[idx]), 1),
                "x": round(float(xs[idx]), 1),
                "y": round(float(ys[idx]), 1),
                "z": tvd_val,
                "color": color,
                "description": desc
            })
            
    return {
        "well_id": well_id,
        "is_active": is_active,
        "surface": {"x": round(float(x0), 1), "y": round(float(y0), 1), "z": 0.0},
        "tvd_max": round(float(tvd_max), 1),
        "total_md": round(float(md[-1]), 1),
        "kop": round(float(kop), 1),
        "trajectory": {
            "x": [round(float(val), 2) for val in xs],
            "y": [round(float(val), 2) for val in ys],
            "z": [round(float(val), 2) for val in depths_z],
            "md": [round(float(val), 2) for val in md],
            "inclination": [round(float(val), 1) for val in inc],
            "azimuth": [round(float(val), 1) for val in az],
            "risk_scores": risk_scores
        },
        "formation_tops": formation_tops
    }

def compute_anti_collision(active_traj: dict, offset_traj: dict):
    pts_a = np.column_stack([active_traj["trajectory"]["x"], active_traj["trajectory"]["y"], active_traj["trajectory"]["z"]])
    pts_b = np.column_stack([offset_traj["trajectory"]["x"], offset_traj["trajectory"]["y"], offset_traj["trajectory"]["z"]])
    
    # Evaluate subsurface points (below surface casing, Z >= 30m) to isolate directional borehole convergence
    sub_mask_a = np.array(active_traj["trajectory"]["z"]) >= 30.0
    sub_mask_b = np.array(offset_traj["trajectory"]["z"]) >= 30.0
    
    if np.any(sub_mask_a) and np.any(sub_mask_b):
        pts_a_eval = pts_a[sub_mask_a]
        pts_b_eval = pts_b[sub_mask_b]
        indices_a = np.where(sub_mask_a)[0]
        indices_b = np.where(sub_mask_b)[0]
    else:
        pts_a_eval = pts_a
        pts_b_eval = pts_b
        indices_a = np.arange(len(pts_a))
        indices_b = np.arange(len(pts_b))
        
    diff = pts_a_eval[:, np.newaxis, :] - pts_b_eval[np.newaxis, :, :]
    dist_matrix = np.linalg.norm(diff, axis=-1)
    min_idx = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
    min_dist = float(dist_matrix[min_idx])
    
    idx_a, idx_b = int(indices_a[min_idx[0]]), int(indices_b[min_idx[1]])
    
    status = "CRITICAL" if min_dist < 60.0 else ("CAUTION" if min_dist < 120.0 else "SAFE")
    separation_factor = round(min_dist / 30.0, 2)
    
    return {
        "offset_well_id": offset_traj["well_id"],
        "min_distance_m": round(min_dist, 1),
        "status": status,
        "separation_factor": separation_factor,
        "active_point": {
            "x": active_traj["trajectory"]["x"][idx_a],
            "y": active_traj["trajectory"]["y"][idx_a],
            "z": active_traj["trajectory"]["z"][idx_a],
            "md": active_traj["trajectory"]["md"][idx_a],
            "tvd": active_traj["trajectory"]["z"][idx_a]
        },
        "offset_point": {
            "x": offset_traj["trajectory"]["x"][idx_b],
            "y": offset_traj["trajectory"]["y"][idx_b],
            "z": offset_traj["trajectory"]["z"][idx_b],
            "md": offset_traj["trajectory"]["md"][idx_b],
            "tvd": offset_traj["trajectory"]["z"][idx_b]
        }
    }

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
