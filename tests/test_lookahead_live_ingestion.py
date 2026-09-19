import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

import sys
import os
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from database import get_db
from main import app
from models import SyntheticEvent

client = TestClient(app)

def test_live_ingestion_multi_hazard_lookahead():
    """
    Simulates ingesting a multi-hazard document (mud loss, gas kick, stuck pipe at different depths)
    and verifies that the Look-Ahead Radar correctly surfaces each distinct hazard as it enters the window.
    """
    mock_db = MagicMock()
    
    # 1. Simulate extraction of 3 distinct events from a single multi-hazard report
    event1 = SyntheticEvent(
        well_id="OIL-MULTI-HAZARD-1",
        depth_start_tvd=1800.0,
        depth_end_tvd=1800.0,
        formation="Tipam",
        event_type="Severe Mud Loss",
        severity="HIGH",
        root_cause="Highly permeable depleted zone",
        mitigation_applied="Pumped LCM pill",
        npt_hours=12.0,
        embedding=[0.0] * 384
    )
    
    event2 = SyntheticEvent(
        well_id="OIL-MULTI-HAZARD-1",
        depth_start_tvd=2100.0,
        depth_end_tvd=2100.0,
        formation="Barail",
        event_type="Gas Kick",
        severity="CRITICAL",
        root_cause="Unexpected overpressure sand",
        mitigation_applied="Shut-in and circulated kill weight mud",
        npt_hours=36.0,
        embedding=[0.0] * 384
    )
    
    event3 = SyntheticEvent(
        well_id="OIL-MULTI-HAZARD-1",
        depth_start_tvd=2245.0,
        depth_end_tvd=2245.0,
        formation="Barail",
        event_type="Differential Sticking",
        severity="HIGH",
        root_cause="High overbalance across permeable zone",
        mitigation_applied="Worked pipe and spotted freeing pill",
        npt_hours=24.0,
        embedding=[0.0] * 384
    )
    
    # Configure mock to return our multi-event list
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [event1, event2, event3]
    
    app.dependency_overrides[get_db] = lambda: mock_db

    # 2. Query Look-Ahead Radar such that all 3 events fall into the window
    # e.g. currently at 1750m, window is 500m (covers 1750m - 2250m)
    response = client.get(
        "/api/wells/OIL-BAGHJAN-1/lookahead",
        params={
            "current_depth": 1750.0,
            "window_meters": 500.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    offset_events = data.get("events", [])
    
    # 3. Assert all 3 distinct hazards are correctly returned
    extracted_types = [ev["event_type"] for ev in offset_events if ev["well_id"] == "OIL-MULTI-HAZARD-1"]
    
    assert "Severe Mud Loss" in extracted_types
    assert "Gas Kick" in extracted_types
    assert "Differential Sticking" in extracted_types
    assert len(extracted_types) == 3
    
    # Print out the events to confirm for the user
    import json
    print("\n\n=== MULTI-HAZARD LOOK-AHEAD RESPONSE ===")
    print(json.dumps(offset_events, indent=2))
    print("========================================\n")
