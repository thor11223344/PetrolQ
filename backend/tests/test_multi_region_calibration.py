import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from simulator import (
    get_well_region_tag,
    get_well_calibrated_baseline,
    WELL_CALIBRATED_BASELINES
)
from services.hybrid_retrieval import get_analog_wells, _extract_formation_set

client = TestClient(app)

REGIONAL_TEST_WELLS = {
    "assam": "OIL-BAGHJAN-1",
    "rajasthan": "OIL-RAJ-BAGHEWALA-1",
    "kg": "OIL-KG-DEEPWATER-1",
    "mizoram": "OIL-MZ-AIZAWL-1"
}

def test_simulator_regional_calibration():
    """Verify all 26 wells have calibrated baselines and proper region detection."""
    assert len(WELL_CALIBRATED_BASELINES) >= 26

    for region, well_id in REGIONAL_TEST_WELLS.items():
        detected_region = get_well_region_tag(well_id)
        assert detected_region == region, f"Expected {region}, got {detected_region} for {well_id}"

        baseline = get_well_calibrated_baseline(well_id)
        assert baseline['depth_tvd'] > 1500.0
        assert baseline['mud_weight'] > 8.0
        assert baseline['rop'] > 0.0
        assert baseline['wob'] > 0.0
        assert baseline['torque'] > 0.0

def test_ml_risk_service_regional_gradients():
    """Verify ML risk fracture gradient and Teale MSE calculation incorporates regional stress."""
    from ml.service import HazardPredictionService
    service = HazardPredictionService()

    # KG deepwater has lower overburden gradient (17.6 ppg) -> smaller margin
    fg_kg, margin_kg = service.calculate_fracture_gradient_margin(
        depth_tvd=2500.0, ecd=14.0, pore_pressure_ppg=12.5, well_id="OIL-KG-DEEPWATER-1"
    )
    # Assam has higher overburden (19.2 ppg)
    fg_assam, margin_assam = service.calculate_fracture_gradient_margin(
        depth_tvd=2500.0, ecd=14.0, pore_pressure_ppg=12.5, well_id="OIL-BAGHJAN-1"
    )
    assert fg_kg > 0.0
    assert fg_assam > 0.0
    # Higher overburden in Assam results in higher fracture gradient than deepwater KG
    assert fg_assam > fg_kg

    # Test risk prediction returns valid risk scores for all regions
    for well_id in REGIONAL_TEST_WELLS.values():
        res = service.predict_risk({
            "well_id": well_id,
            "depth_tvd": 2400.0,
            "wob": 15.0,
            "rop": 10.0,
            "rpm": 90.0,
            "torque": 14000.0,
            "mud_weight": 11.5,
            "ecd": 12.0,
            "flow_out_pct": 100.0,
            "pit_gain_bbl": 0.0,
            "spp_psi": 2500.0
        })
        assert "risk_score" in res
        assert "risk_level" in res
        assert 0.0 <= res["risk_score"] <= 1.0

def test_radar_lookahead_all_regions():
    """Verify /api/wells/{id}/lookahead returns regional horizons and advisories."""
    for region, well_id in REGIONAL_TEST_WELLS.items():
        resp = client.get(f"/api/wells/{well_id}/lookahead", params={"current_depth": 1700.0, "window_meters": 1000.0})
        assert resp.status_code == 200, f"Lookahead failed for {well_id}: {resp.text}"
        data = resp.json()
        assert data["well_id"] == well_id
        assert data["next_formation"] is not None
        assert "upcoming_formations" in data
        assert len(data["upcoming_formations"]) > 0
        assert "advisory_actions" in data
        assert len(data["advisory_actions"]) > 0

def test_ppfg_safe_window_all_regions():
    """Verify /api/wells/{id}/ppfg returns basin-calibrated Eaton curves and casing shoes."""
    for region, well_id in REGIONAL_TEST_WELLS.items():
        resp = client.get(f"/api/wells/{well_id}/ppfg")
        assert resp.status_code == 200, f"PPFG failed for {well_id}: {resp.text}"
        data = resp.json()
        assert data["well_id"] == well_id
        assert data["region"] == region
        assert len(data["pore_pressure_ppg"]) == 80
        assert len(data["fracture_gradient_ppg"]) == 80
        assert len(data["casing_shoes"]) >= 4
        assert len(data["formations"]) >= 3
        assert "active_status" in data
        assert data["active_status"]["mud_weight_ppg"] > 0

def test_correlation_dtw_and_casing():
    """Verify DTW correlation, casing correlation, and stratigraphic cross sections."""
    # DTW within Rajasthan
    resp_dtw = client.get("/api/correlate", params={
        "active_well": "OIL-RAJ-BAGHEWALA-1",
        "offset_well": "OIL-RAJ-TANOT-1"
    })
    assert resp_dtw.status_code == 200
    data_dtw = resp_dtw.json()
    assert len(data_dtw["active_gr"]) > 0
    assert len(data_dtw["offset_gr"]) > 0
    assert "distance" in data_dtw

    # Casing correlation
    for well_id in REGIONAL_TEST_WELLS.values():
        resp_casing = client.get("/api/wells/casing-cement-correlation", params={"active_well": well_id})
        assert resp_casing.status_code == 200
        data_casing = resp_casing.json()
        assert len(data_casing["comparison"][0]["casing_strings"]) >= 4

    # Stratigraphic cross-section
    for well_id in REGIONAL_TEST_WELLS.values():
        resp_strat = client.get("/api/wells/stratigraphic-cross-section", params={"active_well": well_id})
        assert resp_strat.status_code == 200
        data_strat = resp_strat.json()
        assert len(data_strat["wells"]) == 3

def test_rag_analog_wells_and_synthesis():
    """Verify RAG analog well prioritization and AI incident synthesis."""
    # Check analog wells prioritize the same basin
    raj_analogs = get_analog_wells("OIL-RAJ-BAGHEWALA-1", hazard_type="lost_circulation", top_k=4)
    assert any("RAJ" in w for w in raj_analogs), "Rajasthan analog should include Rajasthan wells"

    kg_analogs = get_analog_wells("OIL-KG-DEEPWATER-1", hazard_type="gas_kick", top_k=4)
    assert any("KG" in w for w in kg_analogs), "KG analog should include KG wells"

    mz_analogs = get_analog_wells("OIL-MZ-AIZAWL-1", hazard_type="stuck_pipe", top_k=4)
    assert any("MZ" in w for w in mz_analogs), "Mizoram analog should include Mizoram wells"

    # Formation extraction supports regional formations
    assert "bilara" in _extract_formation_set("Cavernous Bilara Carbonates")
    assert "gumbo" in _extract_formation_set("Swelling Godavari Gumbo Shales")
    assert "bhuban" in _extract_formation_set("Middle Bhuban dipping bed")

    # Incident synthesis endpoint
    synth_resp = client.post("/api/ai/synthesize", json={
        "query": "lost circulation mitigation while drilling cavernous carbonate",
        "well_id": "OIL-RAJ-BAGHEWALA-1",
        "depth_tvd": 2400.0,
        "max_records": 3
    })
    assert synth_resp.status_code == 200
    synth_data = synth_resp.json()
    assert synth_data["status"] == "success"
    assert len(synth_data["recommendations"]) > 0

def test_pre_spud_dossier_all_regions():
    """Verify 1-Click Pre-Spud Dossier generates basin-filtered reports."""
    for region, well_id in REGIONAL_TEST_WELLS.items():
        resp = client.get(f"/api/wells/{well_id}/pre-spud-dossier")
        assert resp.status_code == 200, f"Dossier failed for {well_id}: {resp.text}"
        data = resp.json()
        assert data["target_well"]["well_id"] == well_id
        assert data["target_well"]["region"] == region
        assert len(data["offset_wells"]) > 0
        assert len(data["casing_and_mud_program"]) >= 4
        assert len(data["anti_collision_clearance"]) > 0
        assert "key_primary_threat" in data["executive_summary"]
