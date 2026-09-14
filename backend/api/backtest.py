from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from services.backtest_runner import run_time_travel_backtest, get_available_cases

router = APIRouter()

@router.get("/api/backtest/run")
def get_backtest_run(
    well_id: Optional[str] = Query(None, description="Target well ID. If omitted, runs multi-incident backtest"),
    incident_depth: Optional[float] = Query(None, description="Incident depth in meters TVD"),
    incident_type: Optional[str] = Query(None, description="Incident type (e.g. stuck_pipe, gas_kick, lost_circulation)"),
    run_multi: bool = Query(False, description="Whether to run multi-incident backtest across curated Volve incidents"),
    caution_threshold: float = Query(0.40, description="Caution threshold for elevated risk"),
    critical_threshold: float = Query(0.70, description="Critical hazard probability threshold"),
    precursor_threshold: float = Query(0.25, description="Low threshold for precursor signals")
) -> Dict[str, Any]:
    """
    Time-Travel Backtest Endpoint:
    Replays historical telemetry causally row-by-row up to the incident depth,
    evaluating hazard detection models without lookahead leakage.
    Returns individual replay results and aggregate Wilson score confidence intervals.
    """
    try:
        # If run_multi is True or no specific well_id is provided, run multi-incident backtest
        if run_multi or not well_id or well_id.upper() == "ALL":
            result = run_time_travel_backtest(
                caution_threshold=caution_threshold,
                critical_threshold=critical_threshold,
                precursor_threshold=precursor_threshold
            )
        else:
            result = run_time_travel_backtest(
                well_id=well_id,
                incident_depth_m=incident_depth or 2832.0,
                incident_type=incident_type or "stuck_pipe",
                caution_threshold=caution_threshold,
                critical_threshold=critical_threshold,
                precursor_threshold=precursor_threshold
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest replay failed: {str(e)}")


@router.get("/api/backtest/run-multi")
def get_backtest_run_multi(
    caution_threshold: float = Query(0.40, description="Caution threshold for elevated risk"),
    critical_threshold: float = Query(0.70, description="Critical hazard probability threshold"),
    precursor_threshold: float = Query(0.25, description="Low threshold for precursor signals")
) -> Dict[str, Any]:
    """
    Multi-Incident Backtest Endpoint:
    Replays all curated real historical incidents independently and computes
    an aggregate Wilson confidence interval.
    """
    try:
        return run_time_travel_backtest(
            caution_threshold=caution_threshold,
            critical_threshold=critical_threshold,
            precursor_threshold=precursor_threshold
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-incident backtest failed: {str(e)}")


@router.get("/api/backtest/cases")
def get_backtest_cases() -> List[Dict[str, Any]]:
    """Returns curated documented historical incident cases available for backtest replay."""
    return get_available_cases()

