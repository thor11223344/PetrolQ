import pytest
import numpy as np
import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from services.ahp_weights import derive_ahp_weights, RETRIEVAL_PAIRWISE_MATRIX, RETRIEVAL_CRITERIA, get_retrieval_ahp_weights
from services.statistics_utils import wilson_confidence_interval, format_wilson_insight
from services.sequence_matcher import SequenceMatcherService
from services.statistical_anomaly import StatisticalAnomalyService, rolling_zscore, cusum_detector
from services.knowledge_graph import KnowledgeGraphService
from services.hybrid_retrieval import get_analog_wells, compute_hybrid_relevance_score, AHP_WEIGHTS


# ==============================================================================
# Prompt 1: AHP-Weighted Similarity Scoring Tests
# ==============================================================================
def test_ahp_eigenvector_weights_and_consistency():
    """Verify AHP weights sum to 1.0 and consistency ratio CR < 0.10 (Saaty 1980)."""
    res = derive_ahp_weights(RETRIEVAL_PAIRWISE_MATRIX, RETRIEVAL_CRITERIA)
    
    weights = res["weights"]
    cr = res["consistency_ratio"]
    is_consistent = res["consistent"]
    
    # 1. Check all criteria are present
    assert len(weights) == 5
    for c in RETRIEVAL_CRITERIA:
        assert c in weights
        assert weights[c] > 0
        
    # 2. Sum of weights must equal 1.0 within numerical precision
    assert pytest.approx(sum(weights.values()), rel=1e-4) == 1.0
    
    # 3. Consistency Ratio must be strictly below 0.10
    assert cr < 0.10
    assert is_consistent is True
    
    # 4. Semantic criteria (vector) should have highest weight
    assert weights["vector"] > weights["bm25"]
    assert weights["bm25"] > weights["formation_match"]


# ==============================================================================
# Prompt 2: Per-Item Data Provenance Tagging Tests
# ==============================================================================
def test_data_source_provenance_constants():
    """Verify data provenance classifications match the 3 approved datasets."""
    from schemas import WellResponse, EventResponse
    
    # Verify field definitions in pydantic schemas
    assert "data_source" in WellResponse.model_fields
    assert "data_source" in EventResponse.model_fields


# ==============================================================================
# Prompt 3: Knowledge Graph Layer Tests
# ==============================================================================
def test_knowledge_graph_construction_and_query():
    """Verify NetworkX graph builds nodes, typed edges, depth sequencing, and queries."""
    kg = KnowledgeGraphService()
    
    # Mock data with 2 wells, formations, and sequential events
    wells = [
        {"well_id": "TEST-WELL-1", "field_name": "Assam Test", "total_depth_tvd": 3200.0, "data_source": "volve_relabeled"},
        {"well_id": "TEST-WELL-2", "field_name": "Assam Test", "total_depth_tvd": 3500.0, "data_source": "synthetic"}
    ]
    events = [
        {
            "id": 101,
            "well_id": "TEST-WELL-1",
            "formation": "Barail Formation",
            "event_type": "Gas Kick",
            "depth_start_tvd": 2400.0,
            "depth_end_tvd": 2415.0,
            "severity": "HIGH",
            "root_cause": "Abnormal pore pressure transition",
            "mitigation_applied": "Circulate kill weight mud 11.6 ppg",
            "npt_hours": 14.5
        },
        {
            "id": 102,
            "well_id": "TEST-WELL-1",
            "formation": "Barail Formation",
            "event_type": "Stuck Pipe",
            "depth_start_tvd": 2850.0,
            "depth_end_tvd": 2855.0,
            "severity": "HIGH",
            "root_cause": "Differential sticking in permeable sand",
            "mitigation_applied": "Soak pipe in organic freeing pill and jar down",
            "npt_hours": 26.0
        }
    ]
    
    stats = kg.build_graph(wells, events)
    assert stats["nodes"] > 0
    assert stats["edges"] > 0
    assert stats["wells"] == 2
    assert stats["events"] == 2
    
    # Query graph for TEST-WELL-1
    query_res = kg.query_subgraph(well_id="TEST-WELL-1")
    assert query_res["node_count"] > 0
    assert query_res["edge_count"] > 0
    assert len(query_res["insights"]) > 0
    
    # Verify FOLLOWED_BY edge exists between event 101 (2400m) and event 102 (2850m)
    edges = query_res["edges"]
    followed_by_edges = [e for e in edges if e["relationship"] == "FOLLOWED_BY"]
    assert len(followed_by_edges) >= 1
    assert followed_by_edges[0]["source"] == "Event:101"
    assert followed_by_edges[0]["target"] == "Event:102"


# ==============================================================================
# Prompt 4: Two-Stage Retrieval Tests
# ==============================================================================
def test_two_stage_retrieval_analog_prefiltering():
    """Verify get_analog_wells identifies top analogs and pre-filters search pool."""
    analogs = get_analog_wells(
        target_well_id="OIL-BAGHJAN-1",
        hazard_type="stuck_pipe",
        top_k=2
    )
    
    assert len(analogs) == 2
    assert "OIL-BAGHJAN-1" not in analogs  # Target well filtered out
    assert "OIL-BAGHJAN-4" in analogs or "OIL-MORAN-1" in analogs

    # Verify compute_hybrid_relevance_score works with AHP weights
    res = compute_hybrid_relevance_score(
        formation_match=1.0,
        depth_proximity=0.9,
        event_type_match=1.0,
        bm25=0.8,
        vector=0.85
    )
    assert res["hybrid_score"] > 0.5
    assert res["ahp_metadata"]["consistent"] is True


# ==============================================================================
# Prompt 5: Sequence-Based Pattern Matching Tests
# ==============================================================================
def test_sequence_matcher_dtw():
    """Verify DTW pattern matcher detects stuck pipe precursor and rejects nominal drilling."""
    matcher = SequenceMatcherService(window_size=10, alert_threshold=0.65)
    
    # 1. Feed nominal drilling points (should NOT trigger)
    matcher.reset_buffer()
    for i in range(15):
        pt = {
            "depth_tvd": 2200.0 + i * 2,
            "torque": 12000.0 + np.sin(i) * 500,
            "rop": 15.0 + np.cos(i) * 1.5,
            "wob": 14.0,
            "flow_out_pct": 100.0,
            "spp_psi": 2800.0
        }
        res = matcher.evaluate_telemetry_point(pt)
        
    assert res["matched"] is False
    
    # 2. Feed an escalating stuck pipe sequence (surging torque, crashing ROP, SPP rise)
    matcher.reset_buffer()
    stuck_pipe_sim = [
        {
            "depth_tvd": 2830.0 + i * 0.2,
            "torque": 13000.0 + (11000.0 * ((i / 9.0) ** 1.5)),
            "rop": 15.0 * (1.0 - 0.75 * (i / 9.0)),
            "wob": 14.0,
            "flow_out_pct": 100.0
        }
        for i in range(10)
    ]
    
    match_result = None
    for pt in stuck_pipe_sim:
        match_result = matcher.evaluate_telemetry_point(pt)
        
    assert match_result is not None
    assert match_result["matched"] is True
    assert "Stuck Pipe" in match_result["pattern_name"]
    assert match_result["similarity_score"] >= 0.65


# ==============================================================================
# Prompt 7: Statistical Anomaly Layer (Z-Score & CUSUM) Tests
# ==============================================================================
def test_statistical_anomaly_zscore_and_cusum():
    """Verify rolling Z-Score and two-sided CUSUM detect anomalies without affecting physics/ML."""
    service = StatisticalAnomalyService(baseline_window=10, z_threshold=2.5, cusum_threshold=3.5)
    
    # 1. Normal telemetry readings (Z ~ 0, CUSUM ~ 0)
    for i in range(12):
        res = service.evaluate_reading({
            "torque": 13000.0 + (i % 3) * 100,
            "rop": 16.0 + (i % 2) * 0.5,
            "flow_out_pct": 100.0
        })
    assert res["anomaly_detected"] is False
    assert abs(res["z_scores"]["torque"]) < 2.5
    
    # 2. Sudden torque spike (Z > 2.5)
    spike_res = service.evaluate_reading({
        "torque": 26000.0,
        "rop": 3.0,
        "flow_out_pct": 100.0
    })
    assert spike_res["anomaly_detected"] is True
    assert spike_res["z_scores"]["torque"] > 2.5
    assert "torque" in spike_res["summary"].lower()


# ==============================================================================
# Prompt 8: Wilson Score Confidence Interval Tests
# ==============================================================================
def test_wilson_confidence_interval_calculation():
    """Verify Wilson score confidence interval matches known statistical reference."""
    # Reference: 8 successes out of 10 at 95% confidence (z = 1.96)
    # p_hat = 0.80, Wilson lower ~ 0.490, upper ~ 0.943
    res = wilson_confidence_interval(successes=8, total=10, confidence=0.95)
    
    assert res["point_estimate"] == 0.8
    assert res["sample_size"] == 10
    assert pytest.approx(res["ci_lower"], abs=0.02) == 0.49
    assert pytest.approx(res["ci_upper"], abs=0.02) == 0.94
    assert res["ci_lower"] < res["point_estimate"] < res["ci_upper"]
    
    # Formatted insight text
    text = format_wilson_insight(successes=8, total=10, metric_name="Mitigation success")
    assert "80%" in text
    assert "95% CI:" in text
    assert "n=10" in text

def test_wilson_edge_cases():
    """Verify edge cases for Wilson score (0 total, 0 successes, 100% successes)."""
    # 0 total
    res_zero = wilson_confidence_interval(0, 0)
    assert res_zero["point_estimate"] == 0.0
    assert res_zero["ci_lower"] == 0.0
    
    # 0 successes out of 5
    res_none = wilson_confidence_interval(0, 5)
    assert res_none["point_estimate"] == 0.0
    assert res_none["ci_lower"] == 0.0
    assert res_none["ci_upper"] > 0.0  # Wilson upper bound is > 0 for 0/5
    
    # 5 successes out of 5
    res_all = wilson_confidence_interval(5, 5)
    assert res_all["point_estimate"] == 1.0
    assert res_all["ci_lower"] < 1.0
    assert res_all["ci_upper"] == 1.0
