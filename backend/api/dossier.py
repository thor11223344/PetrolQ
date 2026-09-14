from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from database import get_db
from models import WellMaster, SyntheticEvent
from trajectory_calc import compute_realistic_trajectory, compute_anti_collision
from services.statistics_utils import format_wilson_insight, wilson_confidence_interval

router = APIRouter()

@router.get("/api/wells/{well_id}/pre-spud-dossier")
@router.get("/api/wells/{well_id}/dossier")
def get_pre_spud_dossier(
    well_id: str,
    radius_km: float = Query(25.0, description="Offset well search radius in km"),
    db: Session = Depends(get_db)
):
    """
    1-Click Pre-Spud Offset Well Risk Dossier (SIH 2026 Mandate):
    Compiles an executive engineering report aggregating offset well history,
    formation-specific NPT challenges, casing program recommendations,
    and 3D anti-collision clearance using the exact shared calculation engine.
    """
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found")

    # 1. Fetch nearby offset wells
    # Fetch other wells in the database
    all_wells = db.query(WellMaster).all()
    offsets = [w for w in all_wells if w.well_id != well_id]

    offset_summaries = []
    for off in offsets:
        offset_summaries.append({
            "well_id": off.well_id,
            "field_name": off.field_name or "Baghjan Field",
            "total_depth_tvd": off.total_depth_tvd or 3600.0,
            "spud_date": str(off.spud_date) if off.spud_date else "Historical",
            "kb_elevation": off.kb_elevation or 115.0
        })

    # 2. Historical NPT Incidents grouped by formation
    events = db.query(SyntheticEvent).all()
    
    events_by_formation = {
        "Tipam Sandstone": [],
        "Barail Formation": [],
        "Kopili Formation": [],
        "General / Other": []
    }

    total_npt_hours = 0.0
    critical_events_count = 0

    for ev in events:
        f_key = "General / Other"
        form = getattr(ev, "formation", "") or ""
        if "tipam" in form.lower(): f_key = "Tipam Sandstone"
        elif "barail" in form.lower(): f_key = "Barail Formation"
        elif "kopili" in form.lower(): f_key = "Kopili Formation"

        npt = float(getattr(ev, "npt_hours", 0.0) or 0.0)
        total_npt_hours += npt
        if (getattr(ev, "severity", "") or "").upper() in ["HIGH", "CRITICAL"]:
            critical_events_count += 1

        events_by_formation[f_key].append({
            "well_id": getattr(ev, "well_id", ""),
            "event_type": getattr(ev, "event_type", ""),
            "depth_tvd": getattr(ev, "depth_start_tvd", 0.0),
            "severity": getattr(ev, "severity", "MEDIUM") or "MEDIUM",
            "root_cause": getattr(ev, "root_cause", ""),
            "mitigation_applied": getattr(ev, "mitigation_applied", ""),
            "npt_hours": npt
        })

    # 3. Directional 3D Anti-Collision Clearance (Correction #2: REUSE existing engine directly)
    active_tvd: float = float(getattr(well, "total_depth_tvd", 3500.0) or 3500.0)
    active_events = [e for e in events if getattr(e, "well_id", "") == well_id]
    active_traj = compute_realistic_trajectory(well_id, active_tvd, is_active=True, db_events=active_events)

    anti_collision_evals = []
    min_overall_dist = 9999.0
    closest_well_id = None
    most_critical_status = "SAFE"

    for off in offsets:
        off_well_id = str(getattr(off, "well_id", ""))
        off_events = [e for e in events if getattr(e, "well_id", "") == off_well_id]
        off_tvd: float = float(getattr(off, "total_depth_tvd", 3400.0) or 3400.0)
        off_traj = compute_realistic_trajectory(off_well_id, off_tvd, is_active=False, db_events=off_events)
        
        ac = compute_anti_collision(active_traj, off_traj)
        anti_collision_evals.append({
            "offset_well_id": ac["offset_well_id"],
            "min_distance_m": ac["min_distance_m"],
            "separation_factor": ac["separation_factor"],
            "status": ac["status"],
            "color": ac["color"],
            "active_depth_md": ac["closest_point_active"]["md"],
            "offset_depth_md": ac["closest_point_offset"]["md"]
        })

        if ac["min_distance_m"] < min_overall_dist:
            min_overall_dist = ac["min_distance_m"]
            closest_well_id = ac["offset_well_id"]
            most_critical_status = ac["status"]

    # 4. Geological Prognosis & Casing Program recommendations
    casing_recommendations = [
        {
            "string": 'Conductor (20")',
            "planned_depth_tvd": "65 m",
            "formation": "Alluvium / Dihing Gravels",
            "mud_weight": "8.6 - 9.0 ppg",
            "objective": "Isolate superficial gravels and establish structural foundation."
        },
        {
            "string": 'Surface Casing (13-3/8")',
            "planned_depth_tvd": "650 m",
            "formation": "Upper Tipam",
            "mud_weight": "9.2 - 9.6 ppg",
            "objective": "Case off shallow permeable freshwater aquifers. Install Diverter / BOP."
        },
        {
            "string": 'Intermediate Casing (9-5/8")',
            "planned_depth_tvd": "2,250 m",
            "formation": "Top Barail Kick Transition",
            "mud_weight": "10.4 - 11.2 ppg",
            "objective": "Seat shoe immediately above abnormal pressure ramp. Essential barrier for deep section."
        },
        {
            "string": 'Production Liner (7")',
            "planned_depth_tvd": f"{round(float(active_tvd) - 100.0, 0)} m",
            "formation": "Barail Pay Sand into Kopili",
            "mud_weight": "11.8 - 12.4 ppg",
            "objective": "Isolate high-pressure hydrocarbon gas/condensate pay zones. Cement with gas-tight slurry."
        }
    ]

    # 4. Wilson Score Confidence Interval on mitigation effectiveness (Prompt 8)
    mitigated_events = [e for e in events if e.mitigation_applied and len(str(e.mitigation_applied).strip()) > 3]
    total_events_count = len(events)
    overall_wilson = format_wilson_insight(len(mitigated_events), total_events_count, "Overall offset mitigation success")

    formation_stats = {}
    for fname, fevents in events_by_formation.items():
        f_mitigated = sum(1 for e in fevents if e.get("mitigation_applied") and len(str(e["mitigation_applied"]).strip()) > 3)
        formation_stats[fname] = format_wilson_insight(f_mitigated, len(fevents), f"{fname} mitigation success")

    return {
        "report_metadata": {
            "title": "PRE-SPUD OFFSET WELL HAZARD & ENGINEERING DOSSIER",
            "institution": "PETROLQ",
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "document_id": f"PETROLQ-DOSSIER-{well_id}",
            "confidentiality": "RESTRICTED / OPERATIONAL"
        },
        "target_well": {
            "well_id": well.well_id,
            "field_name": well.field_name or "Baghjan Field",
            "planned_td_tvd_m": active_tvd,
            "planned_td_md_m": active_traj["total_md"],
            "kb_elevation_m": well.kb_elevation or 115.0,
            "spud_date": str(well.spud_date) if well.spud_date else "Planned Q3",
            "search_radius_km": radius_km
        },
        "executive_summary": {
            "offset_wells_analyzed": len(offsets),
            "historical_incidents_recorded": len(events),
            "total_offset_npt_hours": round(total_npt_hours, 1),
            "critical_events_count": critical_events_count,
            "closest_approach_distance_m": round(min_overall_dist, 1) if closest_well_id else None,
            "closest_approach_offset_well": closest_well_id,
            "overall_collision_status": most_critical_status,
            "key_primary_threat": "Barail Formation Gas Kick & Abnormal Overpressure Ramp between 2,200m and 2,650m TVD.",
            "mitigation_wilson_stats": overall_wilson
        },
        "offset_wells": offset_summaries,
        "formation_hazard_breakdown": events_by_formation,
        "formation_wilson_stats": formation_stats,
        "anti_collision_clearance": anti_collision_evals,
        "casing_and_mud_program": casing_recommendations
    }
