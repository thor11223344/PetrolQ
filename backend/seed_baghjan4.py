import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import WellMaster
from database import Base

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()
    try:
        # Check if already exists
        exists = db.query(WellMaster).filter(WellMaster.well_id == 'OIL-BAGHJAN-4').first()
        if exists:
            print("OIL-BAGHJAN-4 already exists.")
            return

        well = WellMaster(
            well_id='OIL-BAGHJAN-4',
            surface_location="POINT(95.187 27.417)", # slightly offset from BAGHJAN-1 (95.185, 27.415)
            field_name='Baghjan Field',
            total_depth_tvd=3500.0
        )
        db.add(well)
        db.commit()
        print("Successfully seeded OIL-BAGHJAN-4!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
