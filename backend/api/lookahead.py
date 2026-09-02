from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import math
import numpy as np
from geoalchemy2.shape import to_shape

from database import get_db
from models import WellMaster, SyntheticEvent, DrillingParam
from ml.service import HazardPredictionService

router = APIRouter()

# Field & Well-specific formation top specifications for the Upper Assam Shelf Basin
WELL_FORMATION_HORIZONS: Dict[str, List[Dict[str, Any]]] = {
    "OIL-BAGHJAN-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1200.0, "color": "#EAB308", "lithology": "Permeable Sandstone / Freshwater Aquifer", "primary_risk": "Seepage & Differential Sticking"},
        {"name": "Barail Formation", "tvd_top": 2400.0, "color": "#F97316", "lithology": "Overpressured Sandstone-Shale Sequence", "primary_risk": "Gas Kick & Severe Lost Circulation"},
        {"name": "Kopili Formation", "tvd_top": 2950.0, "color": "#A855F7", "lithology": "Deep Marine Fissile Shale", "primary_risk": "Shale Swelling & Tight Hole / Packoff"}
    ],
    "OIL-BAGHJAN-4": [
        {"name": "Tipam Sandstone", "tvd_top": 1215.0, "color": "#EAB308", "lithology": "Permeable Sandstone / Freshwater Aquifer", "primary_risk": "Differential Sticking"},
        {"name": "Barail Formation", "tvd_top": 2420.0, "color": "#F97316", "lithology": "Overpressured Gas Sandstone & Coal Sequence", "primary_risk": "Gas Kick & Severe Lost Circulation"},
        {"name": "Kopili Formation", "tvd_top": 2965.0, "color": "#A855F7", "lithology": "Deep Marine Fissile Shale", "primary_risk": "Packoff & Tight Pull"}
    ],
    "OIL-NAHARKATIYA-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1050.0, "color": "#EAB308", "lithology": "Permeable Coarse Sandstone", "primary_risk": "Differential Sticking"},
        {"name": "Barail Formation", "tvd_top": 2040.0, "color": "#F97316", "lithology": "Sand-Shale Alternations with Coal Streaks", "primary_risk": "Gas Kick & Wellbore Instability"},
        {"name": "Kopili Formation", "tvd_top": 2820.0, "color": "#A855F7", "lithology": "Fissile Splintery Shales", "primary_risk": "Severe Lost Circulation & Packoff"}
    ],
    "OIL-MORAN-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1420.0, "color": "#EAB308", "lithology": "Massive Bedded Sandstone", "primary_risk": "Loss of Circulation"},
        {"name": "Barail Formation", "tvd_top": 2580.0, "color": "#F97316", "lithology": "Interbedded Sandstones & Carbonaceous Shale", "primary_risk": "High Pore Pressure Kick & Tight Hole"},
        {"name": "Kopili Formation", "tvd_top": 3080.0, "color": "#A855F7", "lithology": "Dense Overpressured Marine Shale", "primary_risk": "Differential & Mechanical Sticking"}
    ],
    "OIL-DIKOM-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1160.0, "color": "#EAB308", "lithology": "Channel Sandstone with Siltstones", "primary_risk": "Mud Loss & Seepage"},
        {"name": "Barail Formation", "tvd_top": 2240.0, "color": "#F97316", "lithology": "Oligocene Sandstone Reservoirs", "primary_risk": "Kick & Fluid Breakout"},
        {"name": "Kopili Formation", "tvd_top": 2620.0, "color": "#A855F7", "lithology": "Calcareous Shale and Siltstone", "primary_risk": "Lost Circulation"}
    ],
    "OIL-TENGAKHAT-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1100.0, "color": "#EAB308", "lithology": "Sub-surface Aquifer Sand", "primary_risk": "Differential Sticking"},
        {"name": "Barail Formation", "tvd_top": 2120.0, "color": "#F97316", "lithology": "Barail Main Sand Interval", "primary_risk": "Gas Influx"},
        {"name": "Kopili Formation", "tvd_top": 2780.0, "color": "#A855F7", "lithology": "Swelling & Sloughing Shale", "primary_risk": "Tight Pull & Packoff"}
    ],
    "OIL-KOTHALONI-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1250.0, "color": "#EAB308", "lithology": "Fluvial Sandstone", "primary_risk": "Filtrate Loss"},
        {"name": "Barail Formation", "tvd_top": 2320.0, "color": "#F97316", "lithology": "Argillaceous Sandstone", "primary_risk": "Shale Instability & Kick"},
        {"name": "Kopili Formation", "tvd_top": 2720.0, "color": "#A855F7", "lithology": "Fissile Shale", "primary_risk": "Pipe Sticking"}
    ],
    "OIL-HAPJAN-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1280.0, "color": "#EAB308", "lithology": "Massive Aquifer Sands", "primary_risk": "Seepage Loss"},
        {"name": "Barail Formation", "tvd_top": 2360.0, "color": "#F97316", "lithology": "Barail Coal-Shale Sequence", "primary_risk": "Gas Kick & Overpressure"},
        {"name": "Kopili Formation", "tvd_top": 2890.0, "color": "#A855F7", "lithology": "Marine Mudstone", "primary_risk": "Wellbore Cavings"}
    ],
    "OIL-SHALMARI-1": [
        {"name": "Tipam Sandstone", "tvd_top": 1140.0, "color": "#EAB308", "lithology": "Coarse Grained Sand", "primary_risk": "Differential Sticking"},
        {"name": "Barail Formation", "tvd_top": 2210.0, "color": "#F97316", "lithology": "Laminated Sand-Shale", "primary_risk": "Lost Circulation"},
        {"name": "Kopili Formation", "tvd_top": 2690.0, "color": "#A855F7", "lithology": "Compact Shale", "primary_risk": "Tight Hole"}
    ],
}

DEFAULT_HORIZONS = [
    {"name": "Tipam Sandstone", "tvd_top": 1200.0, "color": "#EAB308", "lithology": "Permeable Sandstone / Aquifer", "primary_risk": "Differential Sticking"},
    {"name": "Barail Formation", "tvd_top": 2400.0, "color": "#F97316", "lithology": "Overpressured Sandstone-Shale", "primary_risk": "Gas Kick & Lost Circulation"},
    {"name": "Kopili Formation", "tvd_top": 2950.0, "color": "#A855F7", "lithology": "Deep Marine Fissile Shale", "primary_risk": "Shale Swelling & Packoff"}
]

# Baseline depths when opening each well if telemetry is not yet active
WELL_BASE_DEPTHS = {
    "OIL-BAGHJAN-1": 2240.0,
    "OIL-BAGHJAN-4": 2260.0,
    "OIL-NAHARKATIYA-1": 1920.0,
    "OIL-MORAN-1": 2460.0,
    "OIL-DIKOM-1": 2120.0,
    "OIL-TENGAKHAT-1": 1990.0,
    "OIL-KOTHALONI-1": 2200.0,
    "OIL-HAPJAN-1": 2230.0,
    "OIL-SHALMARI-1": 2080.0,
}

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)

@router.get("/api/wells/{well_id}/lookahead")
def get_lookahead_advisory(
    well_id: str,
    current_depth: Optional[float] = Query(None, description="Current bit TVD depth in meters"),
    window_meters: float = Query(250.0, description="Look-ahead window depth in meters"),
    db: Session = Depends(get_db)
):
    """
    Ahead-of-the-Bit Predictive Hazard Radar:
    Scans the upcoming depth window [current_depth, current_depth + window_meters]
    to forecast formation transitions, correlate historical offset events from geographically
    proximate offset wells, and derive driller recommendations using the unified ML hazard model.
    """
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found")

    # Determine depth to use if not explicitly specified
    if current_depth is None or current_depth <= 0:
        current_depth = WELL_BASE_DEPTHS.get(well_id, 2240.0)

    target_depth = current_depth + window_meters

    # 1. Identify upcoming formations specifically for this well
    horizons = WELL_FORMATION_HORIZONS.get(well_id, DEFAULT_HORIZONS)
    upcoming_formations = []
    next_formation = None
    dist_to_next_formation = None

    for f in horizons:
        if f["tvd_top"] > current_depth:
            dist = round(f["tvd_top"] - current_depth, 1)
            if next_formation is None or dist < dist_to_next_formation:
                next_formation = f["name"]
                dist_to_next_formation = dist
            
            if f["tvd_top"] <= target_depth:
                upcoming_formations.append({
                    "name": f["name"],
                    "tvd_top": f["tvd_top"],
                    "distance_ahead_m": dist,
                    "color": f["color"],
                    "lithology": f["lithology"],
                    "primary_risk": f["primary_risk"]
                })

    # 2. Geospatially correlate offset wells and calculate distances
    well_coords: Dict[str, tuple] = {}
    all_wells = db.query(WellMaster).all()
    for w in all_wells:
        if w.surface_location:
            try:
                geom = to_shape(w.surface_location)
                well_coords[w.well_id] = (geom.y, geom.x)  # (lat, lon)
            except Exception:
                pass

    active_lat_lon = well_coords.get(well_id)

    # Compute distances from active well to all other wells
    offset_distances: Dict[str, float] = {}
    for other_id, (lat, lon) in well_coords.items():
        if other_id != well_id and active_lat_lon:
            offset_distances[other_id] = haversine_km(active_lat_lon[0], active_lat_lon[1], lat, lon)
        else:
            offset_distances[other_id] = 0.0

    # Query offset events in this depth window
    # Exclude the active well itself from its own offset list, unless no offsets exist
    candidate_events = db.query(SyntheticEvent).filter(
        SyntheticEvent.depth_start_tvd <= target_depth,
        SyntheticEvent.depth_end_tvd >= current_depth
    ).all()

    # Separate events into true offsets (other wells) and prioritize nearby wells
    scored_events = []
    for ev in candidate_events:
        dist_km = offset_distances.get(ev.well_id, 999.0)
        is_self = (ev.well_id == well_id)
        scored_events.append({
            "event": ev,
            "distance_km": dist_km,
            "is_self": is_self
        })

    # Sort candidates by:
    # 1. Non-self first (actual offset wells)
    # 2. Proximity (closest distance_km)
    # 3. Severity (CRITICAL > HIGH > MEDIUM)
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    scored_events.sort(key=lambda x: (
        1 if x["is_self"] else 0,
        x["distance_km"],
        severity_order.get((x["event"].severity or "MEDIUM").upper(), 2)
    ))

    # Formatted events list
    horizon_events = []
    kick_count = 0
    loss_count = 0
    stuck_count = 0

    for item in scored_events:
        ev = item["event"]
        dist_km = item["distance_km"]
        etype = ev.event_type or "Operational Incident"
        lower_type = etype.lower()
        if "kick" in lower_type: kick_count += 1
        elif "loss" in lower_type or "lost" in lower_type: loss_count += 1
        elif "stuck" in lower_type or "tight" in lower_type: stuck_count += 1

        horizon_events.append({
            "well_id": ev.well_id,
            "offset_distance_km": dist_km,
            "is_offset": not item["is_self"],
            "event_type": etype,
            "depth_tvd": ev.depth_start_tvd,
            "severity": ev.severity or "MEDIUM",
            "formation": ev.formation or (next_formation or "Barail"),
            "root_cause": ev.root_cause,
            "mitigation": ev.mitigation_applied,
            "npt_hours": ev.npt_hours or 0.0
        })

    # 3. Retrieve latest telemetry to feed the shared ML Hazard model
    latest_param = db.query(DrillingParam).filter(
        DrillingParam.well_id == well_id
    ).order_by(DrillingParam.timestamp.desc()).first()

    if latest_param:
        current_telemetry = {
            "wob": latest_param.wob or 12.0,
            "rpm": latest_param.rpm or 110.0,
            "rop": latest_param.rop or 18.5,
            "torque": latest_param.torque or 12500.0,
            "mud_weight": latest_param.mud_weight or 10.8,
            "ecd": latest_param.ecd or 11.2
        }
    else:
        # Well-specific parameter baselines
        well_telemetry_baselines = {
            "OIL-BAGHJAN-1": {"wob": 14.0, "rpm": 110.0, "rop": 16.5, "torque": 13500.0, "mud_weight": 11.2, "ecd": 11.6},
            "OIL-BAGHJAN-4": {"wob": 14.5, "rpm": 115.0, "rop": 17.0, "torque": 13800.0, "mud_weight": 11.4, "ecd": 11.8},
            "OIL-NAHARKATIYA-1": {"wob": 11.0, "rpm": 95.0, "rop": 13.0, "torque": 10200.0, "mud_weight": 10.4, "ecd": 10.8},
            "OIL-MORAN-1": {"wob": 16.0, "rpm": 120.0, "rop": 19.0, "torque": 15200.0, "mud_weight": 11.8, "ecd": 12.3},
            "OIL-DIKOM-1": {"wob": 12.5, "rpm": 100.0, "rop": 14.5, "torque": 11500.0, "mud_weight": 10.6, "ecd": 11.0},
            "OIL-TENGAKHAT-1": {"wob": 11.5, "rpm": 98.0, "rop": 13.8, "torque": 10800.0, "mud_weight": 10.5, "ecd": 10.9},
            "OIL-KOTHALONI-1": {"wob": 13.0, "rpm": 105.0, "rop": 15.0, "torque": 12000.0, "mud_weight": 10.8, "ecd": 11.2},
            "OIL-HAPJAN-1": {"wob": 13.5, "rpm": 108.0, "rop": 15.5, "torque": 12400.0, "mud_weight": 10.9, "ecd": 11.3},
            "OIL-SHALMARI-1": {"wob": 12.0, "rpm": 102.0, "rop": 14.0, "torque": 11200.0, "mud_weight": 10.6, "ecd": 11.0},
        }
        current_telemetry = well_telemetry_baselines.get(well_id, {
            "wob": 14.0, "rpm": 105.0, "rop": 16.0, "torque": 13200.0, "mud_weight": 11.0, "ecd": 11.4
        })

    # Format offset events for the ML hazard service
    ml_offset_records = [
        {
            "event_type": e["event_type"],
            "depth_start_tvd": e["depth_tvd"],
            "severity": e["severity"],
            "formation": e["formation"]
        }
        for e in horizon_events[:8]
    ]

    # Shared unified ML hazard prediction
    ml_service = HazardPredictionService()
    ml_pred = ml_service.predict_risk(current_telemetry, ml_offset_records)
    
    # Base risk score from ML model
    risk_score = ml_pred.get("risk_score", 0.45)
    hazard_level = ml_pred.get("hazard_level", "MODERATE")
    top_factors = ml_pred.get("top_factors", [])

    # 4. Proactive Driller Advisory Recommendations
    advisory_actions = []
    if dist_to_next_formation is not None and dist_to_next_formation <= 250.0:
        if "Barail" in (next_formation or ""):
            advisory_actions.append({
                "category": "MUD_SYSTEM",
                "priority": "HIGH",
                "action": f"Entering overpressured Barail sequence in {dist_to_next_formation}m for {well_id}. Pre-treat active mud pits to 11.6–12.0 ppg. Verify barite reserve stock."
            })
            advisory_actions.append({
                "category": "WELL_CONTROL",
                "priority": "HIGH",
                "action": "Line up trip tank, function-test annular BOP, and conduct flow check prior to top-of-formation."
            })
        elif "Tipam" in (next_formation or ""):
            advisory_actions.append({
                "category": "DRILLING_FLUID",
                "priority": "MEDIUM",
                "action": f"Approaching high-permeability Tipam Sandstone in {dist_to_next_formation}m. Prepare 30 bbl LCM pill (calcium carbonate / mica) to prevent seepage."
            })
        elif "Kopili" in (next_formation or ""):
            advisory_actions.append({
                "category": "SHALE_STABILITY",
                "priority": "HIGH",
                "action": f"Entering reactive Kopili Shale in {dist_to_next_formation}m. Increase PHPA / glycol inhibitor levels to minimize swelling and packoff."
            })
    
    # Top nearby offset well info
    nearest_offset_str = ""
    for ev in horizon_events:
        if ev.get("is_offset") and ev.get("offset_distance_km", 0) > 0:
            nearest_offset_str = f" Closest offset is {ev['well_id']} ({ev['offset_distance_km']} km away)."
            break

    if kick_count > 0:
        advisory_actions.append({
            "category": "DETECTION",
            "priority": "CRITICAL",
            "action": f"{kick_count} historical kick(s) recorded in nearby offset wells within this depth corridor.{nearest_offset_str} Monitor delta-flow and pit gain thresholds."
        })
    if loss_count > 0:
        advisory_actions.append({
            "category": "HYDRAULICS",
            "priority": "MEDIUM",
            "action": f"{loss_count} historical loss event(s) in offset wells.{nearest_offset_str} Limit flow rate to maintain ECD below formation breakdown pressure."
        })
    if stuck_count > 0:
        advisory_actions.append({
            "category": "MECHANICS",
            "priority": "MEDIUM",
            "action": f"Historical pipe sticking reported in nearby offsets.{nearest_offset_str} Perform wiper trips every 90m and avoid stationary pipe on bottom."
        })

    if not advisory_actions:
        advisory_actions.append({
            "category": "NORMAL_DRILLING",
            "priority": "LOW",
            "action": f"Drilling corridor stable for {well_id}. No critical offset incidents within {window_meters}m window. Maintain standard ROP."
        })

    return {
        "well_id": well_id,
        "current_depth_tvd": round(current_depth, 1),
        "target_depth_tvd": round(target_depth, 1),
        "window_meters": window_meters,
        "next_formation": next_formation,
        "distance_to_next_formation_m": dist_to_next_formation,
        "upcoming_formations": upcoming_formations,
        "horizon_events_count": len(horizon_events),
        "kick_events_count": kick_count,
        "loss_events_count": loss_count,
        "stuck_events_count": stuck_count,
        "events": horizon_events[:8],
        "ml_risk_assessment": {
            "risk_score": risk_score,
            "hazard_level": hazard_level,
            "dominant_threat": ml_pred.get("dominant_threat", "GAS_KICK" if kick_count > 0 else "NORMAL"),
            "top_factors": top_factors
        },
        "advisory_actions": advisory_actions
    }

