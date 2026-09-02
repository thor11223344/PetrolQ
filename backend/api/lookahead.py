from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import numpy as np

from database import get_db
from models import WellMaster, SyntheticEvent, DrillingParam
from ml.service import HazardPredictionService

router = APIRouter()

# Formation specifications for the Upper Assam Shelf Basin
FORMATION_HORIZONS = [
    {"name": "Tipam Sandstone", "tvd_top": 1200.0, "color": "#EAB308", "lithology": "Permeable Sandstone / Freshwater Aquifer", "primary_risk": "Seepage & Differential Sticking"},
    {"name": "Barail Formation", "tvd_top": 2400.0, "color": "#F97316", "lithology": "Overpressured Sandstone-Shale Sequence", "primary_risk": "Gas Kick & Severe Lost Circulation"},
    {"name": "Kopili Formation", "tvd_top": 2950.0, "color": "#A855F7", "lithology": "Deep Marine Fissile Shale", "primary_risk": "Shale Swelling & Tight Hole / Packoff"}
]

@router.get("/api/wells/{well_id}/lookahead")
def get_lookahead_advisory(
    well_id: str,
    current_depth: float = Query(2200.0, description="Current bit TVD depth in meters"),
    window_meters: float = Query(250.0, description="Look-ahead window depth in meters"),
    db: Session = Depends(get_db)
):
    """
    Ahead-of-the-Bit Predictive Hazard Radar:
    Scans the upcoming depth window [current_depth, current_depth + window_meters]
    to forecast formation transitions, correlate historical offset events,
    and derive proactive driller recommendations using the unified ML hazard model.
    """
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found")

    target_depth = current_depth + window_meters

    # 1. Identify upcoming formations in this window
    upcoming_formations = []
    next_formation = None
    dist_to_next_formation = None

    for f in FORMATION_HORIZONS:
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

    # 2. Query historical offset events in this depth window
    # Query events from other wells or field-wide within the depth range
    offset_events = db.query(SyntheticEvent).filter(
        SyntheticEvent.depth_start_tvd <= target_depth,
        SyntheticEvent.depth_end_tvd >= current_depth
    ).all()

    # Formatted events list
    horizon_events = []
    kick_count = 0
    loss_count = 0
    stuck_count = 0

    for ev in offset_events:
        etype = ev.event_type or "Operational Incident"
        lower_type = etype.lower()
        if "kick" in lower_type: kick_count += 1
        elif "loss" in lower_type or "lost" in lower_type: loss_count += 1
        elif "stuck" in lower_type or "tight" in lower_type: stuck_count += 1

        horizon_events.append({
            "well_id": ev.well_id,
            "event_type": etype,
            "depth_tvd": ev.depth_start_tvd,
            "severity": ev.severity or "MEDIUM",
            "formation": ev.formation or "Barail",
            "root_cause": ev.root_cause,
            "mitigation": ev.mitigation_applied,
            "npt_hours": ev.npt_hours or 0.0
        })

    # 3. Retrieve latest telemetry to feed the shared ML Hazard model (Correction #5)
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
        current_telemetry = {
            "wob": 14.0,
            "rpm": 105.0,
            "rop": 16.0,
            "torque": 13200.0,
            "mud_weight": 11.0,
            "ecd": 11.4
        }

    # Format offset events for the ML hazard service
    ml_offset_records = [
        {
            "event_type": e["event_type"],
            "depth_start_tvd": e["depth_tvd"],
            "severity": e["severity"],
            "formation": e["formation"]
        }
        for e in horizon_events
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
    if dist_to_next_formation is not None and dist_to_next_formation <= 200.0:
        if "Barail" in (next_formation or ""):
            advisory_actions.append({
                "category": "MUD_SYSTEM",
                "priority": "HIGH",
                "action": f"Entering overpressured Barail in {dist_to_next_formation}m. Pre-treat active mud pits to 11.6–12.0 ppg. Verify barite reserve stock."
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
                "action": f"Entering high-permeability Tipam in {dist_to_next_formation}m. Prepare 30 bbl LCM pill (calcium carbonate / mica)."
            })
    
    if kick_count > 0:
        advisory_actions.append({
            "category": "DETECTION",
            "priority": "CRITICAL",
            "action": f"{kick_count} historical kick(s) recorded in nearby wells within this depth corridor. Monitor delta-flow and pit gain thresholds."
        })
    if loss_count > 0:
        advisory_actions.append({
            "category": "HYDRAULICS",
            "priority": "MEDIUM",
            "action": f"{loss_count} historical loss event(s) nearby. Limit flow rate to maintain ECD below formation breakdown pressure."
        })
    if stuck_count > 0:
        advisory_actions.append({
            "category": "MECHANICS",
            "priority": "MEDIUM",
            "action": "Historical pipe sticking reported nearby. Perform wiper trips every 90m and avoid stationary pipe on bottom."
        })

    if not advisory_actions:
        advisory_actions.append({
            "category": "NORMAL_DRILLING",
            "priority": "LOW",
            "action": "Drilling conditions stable in current corridor. Maintain standard ROP and parameters."
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
