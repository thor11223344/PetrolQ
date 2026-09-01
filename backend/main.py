from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import cast
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from geoalchemy2.types import Geography
from typing import List

from .database import get_db
from .models import WellMaster, SyntheticEvent, WellLog
from .schemas import WellResponse, EventResponse, WellLogResponse

app = FastAPI(title="eRTMAC-NWIS API", description="Oil & Gas Drilling Data API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/wells/nearby", response_model=List[WellResponse])
def get_nearby_wells(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Radius in kilometers"),
    db: Session = Depends(get_db)
):
    """
    Search for wells within a specified radius (in km) using PostGIS spatial queries.
    """
    # PostGIS geography calculations use meters
    radius_meters = radius_km * 1000.0

    # Build the target point (SRID 4326)
    target_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    # Use ST_DWithin cast to Geography for highly accurate meter-based spatial distance calculation
    wells = db.query(WellMaster).filter(
        ST_DWithin(
            cast(WellMaster.surface_location, Geography),
            cast(target_point, Geography),
            radius_meters
        )
    ).all()

    return wells

@app.get("/api/wells/{well_id}/history")
def get_well_history(
    well_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the event history and well logs for a specific well.
    """
    # Verify the well exists first
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    # Fetch events and logs
    events = db.query(SyntheticEvent).filter(SyntheticEvent.well_id == well_id).all()
    logs = db.query(WellLog).filter(WellLog.well_id == well_id).all()

    # Serialize using Pydantic
    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "logs": [WellLogResponse.model_validate(l) for l in logs]
    }
