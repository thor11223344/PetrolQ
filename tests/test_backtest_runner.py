import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend is in python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.backtest_runner import (
    run_time_travel_backtest,
    get_available_cases,
    load_historical_telemetry,
    HISTORICAL_INCIDENTS_CATALOG
)
from ml.service import HazardPredictionService


def test_causal_replay_no_lookahead_leakage():
    """
    CRITICAL INVARIANT TEST:
    Confirm that the causal replay NEVER has access to telemetry rows beyond
    the current replay depth.
    At replay step N, detector's input must ONLY contain data from steps 1..N,
    and history_params must strictly contain steps 1..N-1, never N+1 onward.
    """
    observed_calls = []
    original_predict = HazardPredictionService.predict_risk

    def spy_predict_risk(self, current_params, history_params=None):
        # Capture deepcopy / snapshot of parameters passed to detector
        curr_depth = float(current_params.get("depth_tvd", 0.0))
        hist_depths = [float(h.get("depth_tvd", 0.0)) for h in (history_params or [])]
        observed_calls.append({
            "current_depth": curr_depth,
            "history_depths": list(hist_depths),
            "history_count": len(hist_depths)
        })
        return original_predict(self, current_params, history_params)

    with patch.object(HazardPredictionService, "predict_risk", spy_predict_risk):
        result = run_time_travel_backtest(
            well_id="OIL-MORAN-1",
            incident_depth_m=2832.0,
            incident_type="stuck_pipe"
        )

    # 1. Assert calls were made in strict chronological/depth sequence
    assert len(observed_calls) > 0, "No replay calls were executed!"
    
    for step_idx, call in enumerate(observed_calls):
        curr_d = call["current_depth"]
        hist_d = call["history_depths"]
        
        # Invariant A: Exactly step_idx prior records were passed (0 for first step, 1 for second, etc.)
        assert call["history_count"] == step_idx, (
            f"Step {step_idx}: Expected {step_idx} history records, but got {call['history_count']}!"
        )
        
        # Invariant B: Every history depth is STRICTLY strictly less than current_depth
        for h_depth in hist_d:
            assert h_depth < curr_d, (
                f"Lookahead leak at step {step_idx}! History depth {h_depth} is >= current depth {curr_d}!"
            )
            
        # Invariant C: Current depth does not exceed incident depth
        assert curr_d <= 2832.0, (
            f"Future leak at step {step_idx}! Current depth {curr_d} exceeds incident depth 2832.0m!"
        )
        
        # Invariant D: History depths match the exact prefix of previous current_depths
        expected_hist = [c["current_depth"] for c in observed_calls[:step_idx]]
        assert hist_d == expected_hist, (
            f"Step {step_idx}: History prefix mismatch! Expected {expected_hist}, got {hist_d}"
        )


def test_backtest_runner_milestones_and_advance_warning():
    """
    Verifies that the backtest runner properly computes advance warning distances
    for all milestones, and that headline result accurately reflects the findings.
    """
    result = run_time_travel_backtest(
        well_id="OIL-MORAN-1",
        incident_depth_m=2832.0,
        incident_type="stuck_pipe"
    )

    assert result["well_id"] == "OIL-MORAN-1"
    assert result["incident_depth_m"] == 2832.0
    assert result["incident_type"] == "stuck_pipe"
    assert "milestones" in result
    assert "headline_result" in result
    assert "replay_curve" in result
    assert len(result["replay_curve"]) > 0

    milestones = result["milestones"]
    for m_name in ["first_precursor_warning", "first_elevated_risk", "first_critical_alert", "first_sequence_match"]:
        assert m_name in milestones
        m_info = milestones[m_name]
        trig = m_info["triggered_at_depth_m"]
        adv = m_info["advance_warning_m"]
        if trig is not None:
            assert trig <= 2832.0
            assert round(2832.0 - trig, 1) == adv
            assert adv >= 0.0

    # For OIL-MORAN-1 stuck pipe reference case:
    # Precursor warning fired at 2792.0m (40m before)
    assert milestones["first_precursor_warning"]["triggered_at_depth_m"] == 2792.0
    assert milestones["first_precursor_warning"]["advance_warning_m"] == 40.0

    # Sequence match fired at 2818.0m (14m before)
    assert milestones["first_sequence_match"]["triggered_at_depth_m"] == 2818.0
    assert milestones["first_sequence_match"]["advance_warning_m"] == 14.0

    # Elevated caution alert fired at 2820.0m (12m before)
    assert milestones["first_elevated_risk"]["triggered_at_depth_m"] == 2820.0
    # Incident selection rationale assertion
    assert "incident_selection_rationale" in result
    assert len(result["incident_selection_rationale"]) > 50
    assert "telemetry" in result["incident_selection_rationale"].lower() or "data" in result["incident_selection_rationale"].lower()


def test_backtest_gas_kick_case():
    """
    Verifies the real DDR gas kick case at OIL-BAGHJAN-4 (2460.0m).
    """
    result = run_time_travel_backtest(
        well_id="OIL-BAGHJAN-4",
        incident_depth_m=2460.0,
        incident_type="gas_kick"
    )
    assert result["milestones"]["first_critical_alert"]["advance_warning_m"] == 6.0
    assert "6.0m before the actual event occurred" in result["headline_result"]
    assert "incident_selection_rationale" in result
    assert "Baghjan" in result["incident_selection_rationale"] or "baghjan" in result["incident_selection_rationale"].lower()


def test_available_cases_catalog():
    """
    Verifies that get_available_cases returns documented real incidents with honest selection rationales.
    """
    cases = get_available_cases()
    assert len(cases) >= 3
    case_ids = [c["case_id"] for c in cases]
    assert "OIL-MORAN-1-stuck-pipe" in case_ids
    assert "OIL-BAGHJAN-4-gas-kick" in case_ids

    for case in cases:
        assert "incident_selection_rationale" in case
        assert len(case["incident_selection_rationale"].strip()) > 40

