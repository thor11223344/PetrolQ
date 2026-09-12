import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import WellLog

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_logs():
    db = SessionLocal()
    try:
        # Check if logs already exist for BAGHJAN-4
        exists = db.query(WellLog).filter(WellLog.well_id == 'OIL-BAGHJAN-4').first()
        if exists:
            print("Logs for OIL-BAGHJAN-4 already exist.")
            return

        # Fetch BAGHJAN-1 logs as a template
        b1_logs = db.query(WellLog).filter(WellLog.well_id == 'OIL-BAGHJAN-1').order_by(WellLog.depth_tvd).all()
        if not b1_logs:
            print("Template logs from OIL-BAGHJAN-1 not found.")
            return

        print(f"Duplicating {len(b1_logs)} logs to OIL-BAGHJAN-4 with slight perturbation...")
        new_logs = []
        for log in b1_logs:
            new_log = WellLog(
                well_id='OIL-BAGHJAN-4',
                depth_tvd=log.depth_tvd,
                gamma_ray=log.gamma_ray * random.uniform(0.9, 1.1) if log.gamma_ray else None,
                resistivity=log.resistivity * random.uniform(0.9, 1.1) if log.resistivity else None,
                sonic=log.sonic * random.uniform(0.9, 1.1) if log.sonic else None,
                density=log.density * random.uniform(0.9, 1.1) if log.density else None,
                formation_top=log.formation_top
            )
            new_logs.append(new_log)
        
        db.bulk_save_objects(new_logs)
        db.commit()
        print("Successfully seeded logs for OIL-BAGHJAN-4!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_logs()
