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
import re
from typing import List, Optional, Dict, Any
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
from api.backtest import router as backtest_router
from services.hybrid_retrieval import (
    DEFAULT_WEIGHTS,
    compute_bm25_score,
    compute_depth_proximity_score,
    compute_formation_match_score,
    compute_event_type_match_score,
    compute_hybrid_relevance_score,
    get_analog_wells
)
from services.ahp_weights import (
    AHP_RETRIEVAL_RESULT,
    AHP_WEIGHTS,
    AHP_CONSISTENCY_RATIO,
    AHP_IS_CONSISTENT
)
from guardrails.guardrails_service import GuardrailsService

class ScoreBreakdown(BaseModel):
    formation_match: float
    depth_proximity: float
    event_type_match: float
    bm25: float
    vector: float

class RAGSearchResponse(BaseModel):
    similarity_score: float
    hybrid_score: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    well_id: str
    depth_tvd: float
    formation: Optional[str] = None
    event_type: str
    root_cause: str
    mitigation_applied: str
    guardrail_verified: bool = True
    data_source: Optional[str] = "synthetic"

def compute_cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

import threading

# Initialize the ML service globally
ml_service = None
_ml_lock = threading.Lock()

def get_ml_service():
    global ml_service
    if ml_service is None:
        with _ml_lock:
            if ml_service is None:
                ml_service = HazardPredictionService()
    return ml_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_service
    # Do NOT instantiate HazardPredictionService at startup to keep boot memory minimal for Render
    yield
    # Clean up on shutdown if necessary

app = FastAPI(title="PetrolQ API", description="Oil & Gas Drilling Data API", lifespan=lifespan)

# Configure CORS - allow all Vercel previews and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://petrol-q.vercel.app"],
    allow_origin_regex=r"https://.*\.vercel\.app",
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
app.include_router(backtest_router)

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
    region: str = Query("all", description="Filter by region (assam, rajasthan, kg, mizoram, all)"),
    db: Session = Depends(get_db)
):
    """
    Search for wells within a specified radius (in km) using PostGIS spatial queries, filtered by region.
    """
    # PostGIS geography calculations use meters
    radius_meters = radius_km * 1000.0

    # Build the target point (SRID 4326)
    target_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    # Use ST_DWithin cast to Geography for highly accurate meter-based spatial distance calculation
    query = db.query(WellMaster).filter(
        ST_DWithin(
            cast(WellMaster.surface_location, Geography),
            cast(target_point, Geography),
            radius_meters
        )
    )
    
    if region != "all":
        if region == "rajasthan":
            query = query.filter(WellMaster.well_id.like("OIL-RAJ-%"))
        elif region == "kg":
            query = query.filter(WellMaster.well_id.like("OIL-KG-%"))
        elif region == "mizoram":
            query = query.filter(WellMaster.well_id.like("OIL-MZ-%"))
        elif region == "assam":
            query = query.filter(
                ~WellMaster.well_id.like("OIL-RAJ-%"),
                ~WellMaster.well_id.like("OIL-KG-%"),
                ~WellMaster.well_id.like("OIL-MZ-%")
            )

    wells = query.all()
    return wells

@app.get("/api/wells/regions")
def get_regions(db: Session = Depends(get_db)):
    """Returns available regions, their center coordinates, well counts, and geological descriptions."""
    all_wells = db.query(WellMaster.well_id).all()
    well_ids = [w[0] for w in all_wells]
    
    counts = {
        "assam": sum(1 for wid in well_ids if not (wid.startswith("OIL-RAJ") or wid.startswith("OIL-KG") or wid.startswith("OIL-MZ"))),
        "rajasthan": sum(1 for wid in well_ids if wid.startswith("OIL-RAJ")),
        "kg": sum(1 for wid in well_ids if wid.startswith("OIL-KG")),
        "mizoram": sum(1 for wid in well_ids if wid.startswith("OIL-MZ"))
    }
    
    return [
        {
            "id": "assam",
            "name": "Upper Assam Shelf",
            "center": [27.4, 95.2],
            "well_count": counts["assam"],
            "description": "Mature oilfield with severe thief-bed losses and high-pressure gas kicks."
        },
        {
            "id": "rajasthan",
            "name": "Rajasthan Basin",
            "center": [27.5, 71.5],
            "well_count": counts["rajasthan"],
            "description": "Desert basin with heavy oil, sand abrasion, and massive lost circulation."
        },
        {
            "id": "kg",
            "name": "KG Deepwater",
            "center": [16.25, 82.40],
            "well_count": counts["kg"],
            "description": "Offshore basin with Shallow Water Flow, gumbo shale, and HPHT overpressures."
        },
        {
            "id": "mizoram",
            "name": "Mizoram Fold Belt",
            "center": [23.72, 92.70],
            "well_count": counts["mizoram"],
            "description": "Tectonically active fold belt with high horizontal stress and stuck pipe risks."
        }
    ]

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
    
    tvd_raw = getattr(well, "total_depth_tvd", None)
    tvd_max = float(tvd_raw) if tvd_raw is not None else 3500.0
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
        
    active_tvd_raw = getattr(active_well, "total_depth_tvd", None)
    active_tvd_max = float(active_tvd_raw) if active_tvd_raw is not None else 3500.0
    active_traj = compute_realistic_trajectory(well_id, active_tvd_max, is_active=True)
    
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
        off_tvd_raw = getattr(off, "total_depth_tvd", None)
        off_tvd_max = float(off_tvd_raw) if off_tvd_raw is not None else 3500.0
        off_traj = compute_realistic_trajectory(str(off.well_id), off_tvd_max, is_active=False)
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
    depth: Optional[float] = Query(None, description="Reference drilling depth TVD in meters for proximity scoring"),
    reference_depth: Optional[float] = Query(None, description="Alias for depth"),
    event_type: Optional[str] = Query(None, description="Optional target event type"),
    well_id: Optional[str] = Query(None, description="Active reference well ID"),
    pre_filter_to_analogs: bool = Query(False, description="Stage 1: Pre-filter candidate event pool to analog wells"),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Multi-Signal Hybrid RAG search endpoint with optional Two-Stage Analog Pre-filtering.
    Computes AHP-derived weighted multi-signal relevance:
    - formation_match (Saaty AHP weight)
    - depth_proximity (Saaty AHP weight)
    - event_type_match (Saaty AHP weight)
    - bm25 lexical score (Saaty AHP weight)
    - vector semantic similarity (Saaty AHP weight)
    Validated by GuardrailsService before returning.
    """
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # Determine reference depth from explicit parameter or extracted from query string
    target_depth = depth if depth is not None else reference_depth
    if target_depth is None:
        depth_match = re.search(r"(\d{3,5})\s*m?", query)
        if depth_match:
            try:
                target_depth = float(depth_match.group(1))
            except ValueError:
                pass

    # Base query for events
    db_query = db.query(SyntheticEvent)
    
    # Prompt 4: Two-Stage Retrieval (Analog Pre-filter)
    if pre_filter_to_analogs:
        ref_well = well_id or "OIL-BAGHJAN-1"
        analog_wells = get_analog_wells(target_well_id=ref_well, hazard_type=event_type or query, top_k=3, db=db)
        if analog_wells:
            db_query = db_query.filter(SyntheticEvent.well_id.in_(analog_wells))
            
    events = db_query.all()
    
    results = []
    for event in events:
        embedding_val = getattr(event, "embedding", None)
        if embedding_val is None or len(embedding_val) == 0:
            continue
            
        # 1. Vector semantic cosine similarity
        sim = compute_cosine_similarity(query_embedding, embedding_val)
        
        depth_val = getattr(event, "depth_start_tvd", None)
        ev_formation = getattr(event, "formation", "") or ""
        ev_type = getattr(event, "event_type", "") or ""
        root_cause = getattr(event, "root_cause", "") or ""
        mitigation = getattr(event, "mitigation_applied", "") or ""

        # 2. Multi-signal component calculations
        f_score = compute_formation_match_score(formation, ev_formation, query)
        d_score = compute_depth_proximity_score(target_depth, depth_val)
        e_score = compute_event_type_match_score(query, ev_type, event_type)
        doc_text = f"{ev_type} {ev_formation} {root_cause} {mitigation}"
        bm25_score = compute_bm25_score(query, doc_text)
        vec_score = float(sim)

        # 3. Hybrid weighted combination (AHP-derived weights)
        hybrid_calc = compute_hybrid_relevance_score(
            formation_match=f_score,
            depth_proximity=d_score,
            event_type_match=e_score,
            bm25=bm25_score,
            vector=vec_score
        )
        final_score = hybrid_calc["hybrid_score"]

        # 4. Deterministic Guardrails validation
        det_truth = {
            "confidence": "high",
            "citations": [{"source_file": f"well_{event.well_id}_history.las", "source_page": 1}],
            "recommended_actions": [mitigation] if mitigation else []
        }
        candidate = {
            "confidence": "high",
            "citations": [{"source_file": f"well_{event.well_id}_history.las", "source_page": 1}],
            "recommendations": [mitigation] if mitigation else [],
            "summary": root_cause,
            "reasoning": ev_type
        }
        guardrail_res = GuardrailsService.validate(det_truth, candidate)
        is_verified = guardrail_res["allowed"]
        mitigation_display = mitigation if is_verified else guardrail_res["validated_response"].get("recommendations", ["Crew manual review required."])[0]

        # Prompt 2: Data Provenance on each search result
        ev_source = getattr(event, "data_source", None) or (
            "force2020_relabeled" if "NAHAR" in str(event.well_id)
            else "volve_relabeled" if ("BAGHJAN" in str(event.well_id) or "MORAN" in str(event.well_id))
            else "synthetic"
        )

        results.append(
            RAGSearchResponse(
                similarity_score=round(final_score, 4),
                hybrid_score=round(final_score, 4),
                score_breakdown=ScoreBreakdown(**{k: round(v, 4) for k, v in hybrid_calc["score_breakdown"].items()}),
                well_id=str(event.well_id),
                depth_tvd=float(depth_val) if depth_val is not None else 0.0,
                formation=ev_formation,
                event_type=ev_type,
                root_cause=root_cause,
                mitigation_applied=mitigation_display,
                guardrail_verified=is_verified,
                data_source=ev_source
            )
        )
        
    # Sort descending by hybrid multi-signal relevance score
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return results[:limit]

@app.get("/api/retrieval/ahp-weights")
def get_ahp_weights():
    """
    Returns the mathematically derived AHP feature weights (Saaty 1980),
    the domain pairwise comparison matrix, and consistency verification metrics.
    """
    return {
        "status": "success",
        "method": "Saaty Analytic Hierarchy Process (AHP, 1980) Principal Eigenvector Method",
        "weights": AHP_RETRIEVAL_RESULT["weights"],
        "consistency_ratio": AHP_RETRIEVAL_RESULT["consistency_ratio"],
        "consistent": AHP_RETRIEVAL_RESULT["consistent"],
        "lambda_max": AHP_RETRIEVAL_RESULT["lambda_max"],
        "criteria": AHP_RETRIEVAL_RESULT["criteria"],
        "pairwise_matrix": AHP_RETRIEVAL_RESULT["pairwise_matrix"],
        "domain_justification": "Stratigraphic formation match and TVD depth proximity are co-equal and dominate over raw NLP lexical matching."
    }

@app.post("/api/predict-risk", response_model=RiskPredictionResponse)
def predict_risk(telemetry: TelemetryInput):
    """
    Real-time ML inference endpoint for drilling hazard prediction.
    Accepts incoming sensor telemetry and returns a risk probability, risk level, 
    and top contributing factors via SHAP.
    """
    global ml_service
    
    ml_svc = get_ml_service()
        
    if not ml_svc:
        raise HTTPException(status_code=503, detail="ML Service is not initialized.")
        
    try:
        # Convert schema to dict
        params = telemetry.model_dump()
        
        # Run prediction
        prediction = ml_svc.predict_risk(params)
        
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

class DemoScenario(BaseModel):
    id: str
    title: str
    well_id: str
    depth: float
    torque: float
    wob: float
    rop: float
    formation: str
    scenario_action: str
    description: str
    suggested_question: str

DEMO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "1",
        "title": "Shallow Stuck Pipe Warning — OIL-MORAN-1",
        "well_id": "OIL-MORAN-1",
        "depth": 2832.0,
        "torque": 22500.0,
        "wob": 18.0,
        "rop": 4.5,
        "formation": "Barail Sandstone/Shale transition",
        "scenario_action": "inject_stuck_pipe",
        "description": "Reproduces the documented differential-sticking incident at 2832m — torque spike, ROP collapse, elevated overpull.",
        "suggested_question": "What historical evidence do we have for stuck pipe risk in this formation, and what mitigation worked previously?"
    },
    {
        "id": "2",
        "title": "Severe Lost Circulation — OIL-MORAN-1",
        "well_id": "OIL-MORAN-1",
        "depth": 1540.0,
        "torque": 14200.0,
        "wob": 12.0,
        "rop": 18.0,
        "formation": "Tipam Sandstone (Upper Permeable Zone)",
        "scenario_action": "inject_lost_circulation",
        "description": "Reproduces the severe mud loss incident at 1540m in Tipam Sandstone — pit level drop, flow-out reduction, fracture window breach.",
        "suggested_question": "What is the recommended LCM pill composition and safe mud weight window for Tipam losses?"
    },
    {
        "id": "3",
        "title": "Abnormal Gas Kick Influx — OIL-NAHARKATIYA-1",
        "well_id": "OIL-NAHARKATIYA-1",
        "depth": 3105.0,
        "torque": 19800.0,
        "wob": 15.0,
        "rop": 22.5,
        "formation": "Kopili Formation Overpressure Ramp",
        "scenario_action": "inject_kick",
        "description": "Reproduces the documented high-pressure gas kick at 3105m in Kopili Formation — rapid pit gain, flow increase, SIDPP pressure spike.",
        "suggested_question": "What are the shut-in drill pipe pressure (SIDPP) precedents and kill mud requirements in Kopili?"
    }
]

@app.get("/api/demo-scenarios", response_model=List[DemoScenario])
def get_demo_scenarios():
    """
    Serves 3 pre-configured realistic demo scenarios directly from backend data
    for 1-click live pitch demonstration.
    """
    return DEMO_SCENARIOS

@app.get("/api/graph/query")
def query_knowledge_graph(
    well_id: str = Query("OIL-BAGHJAN-1", description="Target Well ID"),
    hazard_type: str = Query("stuck_pipe", description="Hazard type (e.g. stuck_pipe, mud_loss, gas_kick)"),
    db: Session = Depends(get_db)
):
    """
    Prompt 3: NetworkX Institutional Knowledge Graph query endpoint.
    Returns entity-relationship subgraph (Wells, Formations, Events, Interventions, Outcomes)
    and synthesized Wilson-confidence institutional insight narrative.
    """
    from services.knowledge_graph import KnowledgeGraphService
    kg = KnowledgeGraphService()
    kg.ensure_graph_built(db)
    return kg.query_hazard_subgraph(well_id=well_id, hazard_type=hazard_type)

@app.websocket("/api/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    Centralized multi-client WebSocket telemetry endpoint.
    All connected browser clients receive synchronized live streaming updates.
    """
    await ws_manager.connect(websocket)
    global ml_service
    
    # Send current state immediately on connect
    ml_svc = get_ml_service()
    current_status = telemetry_simulator.get_status()
    current_params = current_status["current_params"]
    prediction = ml_svc.predict_risk(current_params)
    
    from services.sequence_matcher import SequenceMatcherService
    seq_matcher = SequenceMatcherService()
    seq_matcher.add_reading(current_params)
    initial_seq_match = seq_matcher.evaluate_window(similarity_threshold=75.0)

    try:
        await websocket.send_json({
            "status": "success",
            "data": current_params,
            "prediction": prediction,
            "sequence_match": initial_seq_match,
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
                ml_svc = get_ml_service()
                from fastapi.concurrency import run_in_threadpool
                prediction = await run_in_threadpool(ml_svc.predict_risk, params)
                
                # Prompt 5: Temporal Sequence Matching evaluation
                seq_matcher.add_reading(params)
                seq_match = seq_matcher.evaluate_window(similarity_threshold=75.0)

                # Send isolated prediction response back to THIS specific client connection
                await websocket.send_json({
                    "status": "success",
                    "data": params,
                    "prediction": prediction,
                    "sequence_match": seq_match,
                    "scenario": params.get("scenario", "normal")
                })
            except json.JSONDecodeError:
                await websocket.send_json({"status": "error", "message": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

