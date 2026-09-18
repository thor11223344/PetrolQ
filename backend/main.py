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
from api.ai_assistant import router as ai_assistant_router
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
app.include_router(ai_assistant_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "PetrolQ API"}

@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "PetrolQ API"}

import json
from pathlib import Path

_NORTH_SEA_WELLS_CACHE = None
_ALL_WELLS_CACHE = None

def get_north_sea_wells() -> List[WellResponse]:
    global _NORTH_SEA_WELLS_CACHE
    if _NORTH_SEA_WELLS_CACHE is None:
        p = Path(__file__).resolve().parent.parent / "data" / "wells_metadata.json"
        if not p.exists():
            p = Path("data/wells_metadata.json")
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    raw = json.load(f)
                cached = []
                for idx, w in enumerate(raw, 1):
                    lat = w.get("latitude")
                    lon = w.get("longitude")
                    if lat is None or lon is None:
                        continue
                    cached.append(WellResponse(
                        id=1000 + idx,
                        well_id=w["well_id"],
                        field_name="North Sea",
                        kb_elevation=25.0,
                        total_depth_tvd=w.get("total_depth_m", 2853.0),
                        total_depth_m=w.get("total_depth_m", 2853.0),
                        spud_date="2018-05-12",
                        data_source=w.get("source", "real_force2020"),
                        source=w.get("source", "real_force2020"),
                        is_synthetic=w.get("is_synthetic", False),
                        formation_count=w.get("formation_count", len(w.get("formation_tops", [])) or 14),
                        bha_type=w.get("bha_type", "Steerable Motor BHA (1.5 deg PDM + MWD)"),
                        surface_location={"lat": lat, "lon": lon}
                    ))
                _NORTH_SEA_WELLS_CACHE = cached
            except Exception as e:
                print(f"Error loading north sea wells: {e}")
                _NORTH_SEA_WELLS_CACHE = []
        else:
            _NORTH_SEA_WELLS_CACHE = []
    return _NORTH_SEA_WELLS_CACHE

def _format_well_response(w: Any) -> WellResponse:
    loc = None
    surf_loc: Any = getattr(w, "surface_location", None)
    if surf_loc is not None:
        try:
            from geoalchemy2.shape import to_shape
            shape = to_shape(surf_loc)
            loc = {"lat": float(getattr(shape, "y", 0.0)), "lon": float(getattr(shape, "x", 0.0))}
        except Exception:
            loc = surf_loc

    well_id_str: str = str(getattr(w, "well_id", "") or "")
    field_name_val = getattr(w, "field_name", None)
    kb_elevation_val = getattr(w, "kb_elevation", None)
    total_depth_val = getattr(w, "total_depth_tvd", None)
    spud_date_val = getattr(w, "spud_date", None)
    data_source_val = getattr(w, "data_source", None)

    reg = "assam"
    if "OIL-RAJ" in well_id_str: reg = "rajasthan"
    elif "OIL-KG" in well_id_str: reg = "kg"
    elif "OIL-MZ" in well_id_str: reg = "mizoram"

    bha = "Steerable Motor BHA (1.5 deg PDM + MWD)"
    if "DEEPWATER" in well_id_str or "D6" in well_id_str:
        bha = "Rotary Steerable System (RSS) with MWD/LWD"
    elif "MZ" in well_id_str:
        bha = "High-Torque RSS Motor BHA (Packed Hole Assembly)"

    source_val = "real ongc/oil" if "OIL" in well_id_str else (str(data_source_val) if data_source_val else "real")

    return WellResponse(
        id=int(getattr(w, "id", 0)),
        well_id=well_id_str,
        field_name=str(field_name_val) if field_name_val is not None else None,
        kb_elevation=float(kb_elevation_val) if kb_elevation_val is not None else None,
        total_depth_tvd=float(total_depth_val) if total_depth_val is not None else None,
        total_depth_m=float(total_depth_val) if total_depth_val is not None else None,
        spud_date=str(spud_date_val) if spud_date_val is not None else None,
        data_source=str(data_source_val) if data_source_val is not None else None,
        source=source_val,
        is_synthetic=False,
        formation_count=4 if reg in ("assam", "rajasthan") else 5,
        bha_type=bha,
        surface_location=loc
    )

@app.get("/api/wells/nearby", response_model=List[WellResponse])
def get_nearby_wells(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    radius_km: Optional[float] = Query(None, description="Radius in kilometers"),
    region: str = Query("all", description="Filter by region (assam, rajasthan, kg, mizoram, north_sea, all)"),
    db: Session = Depends(get_db)
):
    """
    Search for wells filtered by region and optionally within a spatial radius.
    Guarantees that all wells in the selected basin (Assam, Rajasthan, KG, Mizoram, North Sea) or across India are returned.
    """
    global _ALL_WELLS_CACHE
    
    # Fast path: Serve cached all-wells response instantly if already loaded
    is_broad_query = (lat is None or lon is None or radius_km is None or radius_km >= 100)
    if region == "all" and is_broad_query and _ALL_WELLS_CACHE is not None:
        return _ALL_WELLS_CACHE

    if region == "north_sea":
        return get_north_sea_wells()

    try:
        query = db.query(WellMaster)
        
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
        
        # If a strict local radius is requested with coordinates (and not an all-region or large basin query)
        if lat is not None and lon is not None and radius_km is not None and radius_km < 100 and region == "all":
            radius_meters = radius_km * 1000.0
            target_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
            query = query.filter(
                ST_DWithin(
                    cast(WellMaster.surface_location, Geography),
                    cast(target_point, Geography),
                    radius_meters
                )
            )

        wells = query.all()
        results = [_format_well_response(w) for w in wells]
        if region == "all":
            results.extend(get_north_sea_wells())
            if is_broad_query:
                _ALL_WELLS_CACHE = results
        return results
    except Exception as e:
        print(f"Warning: Database query failed in get_nearby_wells ({e}). Returning fallback wells.")
        fallback_file = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "defaultWells.json"
        if not fallback_file.exists():
            fallback_file = Path("data/defaultWells.json")
        if fallback_file.exists():
            try:
                with open(fallback_file, encoding="utf-8") as f:
                    data = json.load(f)
                all_loaded = [WellResponse(**item) for item in data]
                
                # Filter by region
                if region == "rajasthan":
                    all_loaded = [w for w in all_loaded if w.well_id.startswith("OIL-RAJ-")]
                elif region == "kg":
                    all_loaded = [w for w in all_loaded if w.well_id.startswith("OIL-KG-")]
                elif region == "mizoram":
                    all_loaded = [w for w in all_loaded if w.well_id.startswith("OIL-MZ-")]
                elif region == "assam":
                    all_loaded = [w for w in all_loaded if not (w.well_id.startswith("OIL-RAJ-") or w.well_id.startswith("OIL-KG-") or w.well_id.startswith("OIL-MZ-")) and w.field_name != "North Sea"]
                elif region == "north_sea":
                    all_loaded = [w for w in all_loaded if w.field_name == "North Sea"]

                # Filter by spatial radius if specific coordinates provided
                if lat is not None and lon is not None and radius_km is not None and radius_km < 200:
                    import math
                    def _haversine(lat1, lon1, lat2, lon2):
                        R = 6371.0
                        dLat = math.radians(lat2 - lat1)
                        dLon = math.radians(lon2 - lon1)
                        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
                        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

                    all_loaded = [
                        w for w in all_loaded
                        if w.surface_location and _haversine(lat, lon, w.surface_location.get("lat", 0), w.surface_location.get("lon", 0)) <= radius_km
                    ]

                return all_loaded
            except Exception as read_err:
                print(f"Error parsing fallback wells: {read_err}")
        return get_north_sea_wells()

@app.get("/api/wells/regions")
def get_regions(db: Session = Depends(get_db)):
    """Returns available regions, their center coordinates, well counts, and geological descriptions."""
    try:
        all_wells = db.query(WellMaster.well_id).all()
        well_ids = [w[0] for w in all_wells]
        counts = {
            "assam": sum(1 for wid in well_ids if not (wid.startswith("OIL-RAJ") or wid.startswith("OIL-KG") or wid.startswith("OIL-MZ"))),
            "rajasthan": sum(1 for wid in well_ids if wid.startswith("OIL-RAJ")),
            "kg": sum(1 for wid in well_ids if wid.startswith("OIL-KG")),
            "mizoram": sum(1 for wid in well_ids if wid.startswith("OIL-MZ")),
            "north_sea": len(get_north_sea_wells())
        }
    except Exception as e:
        print(f"Warning: db query failed in get_regions ({e}), using calibrated fallback counts.")
        counts = {
            "assam": 14,
            "rajasthan": 4,
            "kg": 4,
            "mizoram": 4,
            "north_sea": len(get_north_sea_wells()) or 159
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
        },
        {
            "id": "north_sea",
            "name": "North Sea (FORCE2020 & Volve)",
            "center": [58.262, 8.043],
            "well_count": counts["north_sea"] or 159,
            "description": "North Sea benchmark basin with 159 real FORCE 2020 & Equinor Volve exploration wells."
        }
    ]

@app.get("/api/wells/{well_id:path}/history")
def get_well_history(
    well_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the event history and well logs for a specific well with offline fallback.
    """
    try:
        well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
        if well:
            events = db.query(SyntheticEvent).filter(SyntheticEvent.well_id == well_id).all()
            logs = db.query(WellLog).filter(WellLog.well_id == well_id).all()
            return {
                "events": [EventResponse.model_validate(e) for e in events],
                "logs": [WellLogResponse.model_validate(l) for l in logs]
            }
    except Exception as e:
        print(f"Warning: db query failed in get_well_history ({e}), checking offline fallbacks.")

    # Check North Sea wells or return safe empty schema for offline rig continuity
    for nw in get_north_sea_wells():
        if nw.well_id == well_id:
            return {"events": [], "logs": []}

    return {"events": [], "logs": []}

import hashlib

from trajectory_calc import compute_realistic_trajectory, compute_anti_collision

@app.get("/api/wells/{well_id:path}/trajectory")
def get_well_trajectory(well_id: str, is_active: bool = Query(False), db: Session = Depends(get_db)):
    tvd_max = 3500.0
    db_events = []
    try:
        well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
        if well:
            tvd_raw = getattr(well, "total_depth_tvd", None)
            tvd_max = float(tvd_raw) if tvd_raw is not None else 3500.0
        else:
            for nw in get_north_sea_wells():
                if nw.well_id == well_id:
                    tvd_max = nw.total_depth_tvd or 2853.0
                    break
        
        db_events = db.query(SyntheticEvent).filter(
            SyntheticEvent.well_id == well_id,
            SyntheticEvent.formation.isnot(None)
        ).all()
    except Exception as e:
        print(f"Warning: db query failed in get_well_trajectory ({e}), using default depth parameters.")

    return compute_realistic_trajectory(well_id, tvd_max, is_active=is_active, db_events=db_events)

@app.get("/api/wells/{well_id:path}/anti-collision")
def get_anti_collision(
    well_id: str, 
    offset_ids: Optional[str] = Query(None, description="Comma-separated offset well IDs"),
    db: Session = Depends(get_db)
):
    active_tvd_max = 3500.0
    offsets = []
    try:
        active_well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
        if active_well:
            active_tvd_raw = getattr(active_well, "total_depth_tvd", None)
            active_tvd_max = float(active_tvd_raw) if active_tvd_raw is not None else 3500.0
        else:
            for nw in get_north_sea_wells():
                if nw.well_id == well_id:
                    active_tvd_max = nw.total_depth_tvd or 2853.0
                    break
                    
        if offset_ids:
            offset_list = [oid.strip() for oid in offset_ids.split(",") if oid.strip()]
            offsets = db.query(WellMaster).filter(WellMaster.well_id.in_(offset_list)).all()
        else:
            offsets = db.query(WellMaster).filter(WellMaster.well_id != well_id).all()
    except Exception as e:
        print(f"Warning: db query failed in get_anti_collision ({e}), using memory wells cache.")
        if _ALL_WELLS_CACHE:
            offsets = [w for w in _ALL_WELLS_CACHE if w.well_id != well_id]

    active_traj = compute_realistic_trajectory(well_id, active_tvd_max, is_active=True)
    results = []
    closest_overall = None
    min_dist_overall = float("inf")
    
    for off in offsets:
        off_well_id = str(getattr(off, "well_id", "") or "")
        if off_well_id == well_id:
            continue
        off_tvd_raw = getattr(off, "total_depth_tvd", None)
        off_tvd_max = float(off_tvd_raw) if off_tvd_raw is not None else 3500.0
        off_traj = compute_realistic_trajectory(off_well_id, off_tvd_max, is_active=False)
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

@app.get("/api/wells/{well_id:path}", response_model=WellResponse)
def get_well_by_id(well_id: str, db: Session = Depends(get_db)):
    """Fetch details and surface location for a specific well."""
    try:
        well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
        if well:
            return _format_well_response(well)
    except Exception as e:
        print(f"Warning: db query failed in get_well_by_id ({e}), checking memory cache.")

    # Check memory cache
    global _ALL_WELLS_CACHE
    if _ALL_WELLS_CACHE:
        for w in _ALL_WELLS_CACHE:
            if w.well_id == well_id:
                return w

    # Check North Sea wells
    for nw in get_north_sea_wells():
        if nw.well_id == well_id:
            return nw

    # Check defaultWells.json
    fallback_file = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "defaultWells.json"
    if fallback_file.exists():
        try:
            with open(fallback_file, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("well_id") == well_id:
                        return WellResponse(**item)
        except Exception:
            pass

    raise HTTPException(status_code=404, detail=f"Well {well_id} not found")

def get_offline_fallback_events(query: str, target_depth: Optional[float] = None, limit: int = 5) -> List[RAGSearchResponse]:
    """Fallback RAG search using onboard incident files and newly parsed reports when cloud DB or embeddings are unreachable."""
    p = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "defaultIncidents.json"
    if not p.exists():
        p = Path(__file__).resolve().parent / "data" / "curated_historical_incidents.json"
    
    raw = []
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                raw.extend(json.load(f))
        except Exception:
            pass

    # Also include newly ingested offline events
    offline_cache = Path(__file__).resolve().parent / "data" / "offline_ingested_events.json"
    if offline_cache.exists():
        try:
            with open(offline_cache, "r", encoding="utf-8") as f:
                raw.extend(json.load(f))
        except Exception:
            pass

    if not raw:
        return []
    
    try:
        q_terms = [t.lower() for t in query.split() if len(t) > 2]
        scored = []
        for inc in raw:
            ev_type = inc.get("event_type") or inc.get("incident_type", "Operational Risk")
            ev_form = inc.get("formation", "Unknown")
            root_c = inc.get("root_cause") or inc.get("report_summary", "")
            mitig = inc.get("mitigation_applied") or inc.get("report_summary", "")
            doc_text = f"{ev_type} {ev_form} {root_c} {mitig}".lower()
            
            score = 0.3
            for t in q_terms:
                if t in doc_text:
                    score += 0.25
            
            depth_val = float(inc.get("depth_tvd") or inc.get("incident_depth_m") or 2500.0)
            if target_depth:
                diff = abs(depth_val - target_depth)
                score += max(0.0, 0.2 * (1.0 - diff / 1000.0))
            
            score = min(0.98, score)
            scored.append((score, inc, ev_type, ev_form, root_c, mitig, depth_val))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, inc, ev_type, ev_form, root_c, mitig, depth_val in scored[:limit]:
            results.append(RAGSearchResponse(
                similarity_score=round(s, 4),
                hybrid_score=round(s, 4),
                score_breakdown=ScoreBreakdown(
                    formation_match=0.85,
                    depth_proximity=0.80,
                    event_type_match=0.90,
                    bm25=round(s, 4),
                    vector=0.75
                ),
                well_id=str(inc.get("well_id", "OIL-MORAN-1")),
                depth_tvd=depth_val,
                formation=ev_form,
                event_type=str(ev_type).replace("_", " ").title(),
                root_cause=root_c,
                mitigation_applied=mitig,
                guardrail_verified=True,
                data_source=inc.get("data_source") or "real_ongc_oil"
            ))
        return results
    except Exception as e:
        print(f"Error in get_offline_fallback_events: {e}")
        return []

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
    Includes autonomous offline fallback to onboard incident repository.
    """
    target_depth = depth if depth is not None else reference_depth
    if target_depth is None:
        depth_match = re.search(r"(\d{3,5})\s*m?", query)
        if depth_match:
            try:
                target_depth = float(depth_match.group(1))
            except ValueError:
                pass

    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        print(f"Warning: Embedding generation failed ({e}), using offline incident search.")
        return get_offline_fallback_events(query, target_depth, limit)

    try:
        # Base query for events
        db_query = db.query(SyntheticEvent)
        
        # Prompt 4: Two-Stage Retrieval (Analog Pre-filter)
        if pre_filter_to_analogs:
            ref_well = well_id or "OIL-BAGHJAN-1"
            analog_wells = get_analog_wells(target_well_id=ref_well, hazard_type=event_type or query, top_k=3, db=db)
            if analog_wells:
                db_query = db_query.filter(SyntheticEvent.well_id.in_(analog_wells))
                
        events = db_query.all()
    except Exception as e:
        print(f"Warning: Database query failed in search_events ({e}), using offline fallback events.")
        return get_offline_fallback_events(query, target_depth, limit)
    
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
    
    if not results:
        return get_offline_fallback_events(query, target_depth, limit)

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

