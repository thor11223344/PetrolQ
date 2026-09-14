import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import SessionLocal
from models import WellMaster
from sqlalchemy import text

REGIONAL_WELLS = [
    {
        "well_id": "OIL-RAJ-BAGHEWALA-1",
        "field_name": "Rajasthan Basin",
        "kb_elevation": 180.0,
        "total_depth_tvd": 3100.0,
        "spud_date": "2024-03-15",
        "surface_lat": 27.95,
        "surface_lon": 72.10,
        "data_source": "rajasthan_basin"
    },
    {
        "well_id": "OIL-RAJ-TANOT-1",
        "field_name": "Rajasthan Basin",
        "kb_elevation": 140.0,
        "total_depth_tvd": 2900.0,
        "spud_date": "2024-04-10",
        "surface_lat": 27.30,
        "surface_lon": 70.80,
        "data_source": "jaisalmer_basin"
    },
    {
        "well_id": "OIL-KG-DEEPWATER-1",
        "field_name": "KG Deepwater",
        "kb_elevation": 25.0,
        "total_depth_tvd": 4500.0,
        "spud_date": "2024-05-01",
        "surface_lat": 16.25,
        "surface_lon": 82.40,
        "data_source": "kg_deepwater"
    },
    {
        "well_id": "OIL-MZ-AIZAWL-1",
        "field_name": "Mizoram Fold Belt",
        "kb_elevation": 950.0,
        "total_depth_tvd": 4200.0,
        "spud_date": "2024-06-12",
        "surface_lat": 23.72,
        "surface_lon": 92.70,
        "data_source": "mizoram_belt"
    }
]

def seed_regional_wells():
    session = SessionLocal()
    try:
        print("Upserting regional expansion wells into well_master...")
        for w in REGIONAL_WELLS:
            existing = session.query(WellMaster).filter(WellMaster.well_id == w["well_id"]).first()
            point_wkt = f"SRID=4326;POINT({w['surface_lon']} {w['surface_lat']})"
            
            if existing:
                print(f"Updating existing well: {w['well_id']}")
                existing.field_name = w["field_name"]
                existing.kb_elevation = w["kb_elevation"]
                existing.total_depth_tvd = w["total_depth_tvd"]
                existing.spud_date = w["spud_date"]
                existing.data_source = w["data_source"]
                existing.surface_location = point_wkt
            else:
                print(f"Inserting new well: {w['well_id']}")
                new_well = WellMaster(
                    well_id=w["well_id"],
                    field_name=w["field_name"],
                    kb_elevation=w["kb_elevation"],
                    total_depth_tvd=w["total_depth_tvd"],
                    spud_date=w["spud_date"],
                    data_source=w["data_source"],
                    surface_location=point_wkt
                )
                session.add(new_well)
        session.commit()
        print("Successfully seeded all regional wells!")
        
        # Verify
        all_wells = session.query(WellMaster).all()
        print(f"Total wells in database: {len(all_wells)}")
        for aw in all_wells:
            print(f" - {aw.well_id} ({aw.field_name})")
    except Exception as e:
        session.rollback()
        print(f"Error seeding regional wells: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_regional_wells()
