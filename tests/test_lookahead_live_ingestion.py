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

def test_live_ingestion_to_lookahead_radar():
    """
    Simulates ingesting a PDF event (TENGAKHAT-1 at 2245m) and verifies 
    that the Look-Ahead Radar surfaces it for a nearby active well.
    """
    # 1. Mock the DB session to return our new event
    mock_db = MagicMock()
    
    new_event = SyntheticEvent(
        well_id="OIL-TENGAKHAT-1",
        depth_start_tvd=2245.0,
        depth_end_tvd=2245.0,
        formation="Tipam",
        event_type="Differential Sticking",
        severity="HIGH",
        root_cause="High overbalance in depleted permeable Tipam sand",
        mitigation_applied="Pumped nut-plug pill and reduced mud weight",
        npt_hours=24.5,
        embedding=[0.0] * 384
    )
    
    # Configure mock to return our event when querying SyntheticEvent
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [new_event]
    
    app.dependency_overrides[get_db] = lambda: mock_db

    
    # 2. Call the Look-Ahead Radar API as a different nearby well
    # Current depth is 2200, lookahead is 500 (so 2200 to 2700). 2245m is within range.
    response = client.get(
        "/api/wells/OIL-BAGHJAN-1/lookahead",
        params={
            "current_depth": 2200.0,
            "window_meters": 500.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 3. Assert the Lookahead returns the new event
    offset_events = data.get("events", [])
    
    # Check if any returned event corresponds to the ingested one
    found_event = None
    for ev in offset_events:
        if ev["well_id"] == "OIL-TENGAKHAT-1" and ev["event_type"] == "Differential Sticking":
            found_event = ev
            break
            
    assert found_event is not None, "Newly ingested TENGAKHAT-1 event was not found in Look-Ahead Radar!"
    assert found_event["depth_tvd"] == 2245.0
    assert found_event["severity"] == "HIGH"
