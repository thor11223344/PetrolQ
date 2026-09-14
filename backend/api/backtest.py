from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from services.backtest_runner import run_time_travel_backtest, get_available_cases

router = APIRouter()

@router.get("/api/backtest/run")
def get_backtest_run(
    well_id: str = Query("OIL-MORAN-1", description="Target well ID"),
    incident_depth: float = Query(2832.0, description="Incident depth in meters TVD"),
    incident_type: str = Query("stuck_pipe", description="Incident type (e.g. stuck_pipe, gas_kick, lost_circulation)"),
    caution_threshold: float = Query(0.40, description="Caution threshold for elevated risk"),
    critical_threshold: float = Query(0.70, description="Critical hazard probability threshold"),
    precursor_threshold: float = Query(0.25, description="Low threshold for precursor signals")
) -> Dict[str, Any]:
    """
    Time-Travel Backtest Endpoint:
    Replays historical telemetry causally row-by-row up to the incident depth,
    evaluating hazard detection models without lookahead leakage.
    Returns milestone detection depths, advance warning distance in meters,
    headline result, and replay curve points for UI visualization.
    """
    try:
        result = run_time_travel_backtest(
            well_id=well_id,
            incident_depth_m=incident_depth,
            incident_type=incident_type,
            caution_threshold=caution_threshold,
            critical_threshold=critical_threshold,
            precursor_threshold=precursor_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest replay failed: {str(e)}")


@router.get("/api/backtest/cases")
def get_backtest_cases() -> List[Dict[str, Any]]:
    """Returns curated documented historical incident cases available for backtest replay."""
    return get_available_cases()
