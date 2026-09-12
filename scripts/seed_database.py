import os
import sys
from typing import Any, cast
import pandas as pd
from pathlib import Path
import logging

# Setup path so we can import from backend and config modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "backend"))

import numpy as np
from database import engine, Base, SessionLocal
from models import WellMaster, DrillingParam, WellLog, SyntheticEvent
from scripts.config import PROCESSED_DATA_DIR, logger

def seed_database():
    logger.info("Initializing database tables...")
    try:
        # Create all tables defined in models.py
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully (or already exist).")
    except Exception as e:
        logger.error(f"Failed to create tables. Ensure Postgres is running and extensions (postgis, vector) are installed. Error: {e}")
        return

    session = SessionLocal()

    # 1. Ingest wells_master.csv
    try:
        logger.info("Ingesting wells_master.csv...")
        wells_path = PROCESSED_DATA_DIR / "wells_master.csv"
        if wells_path.exists():
            df_wells = pd.read_csv(wells_path)
            
            # Convert surface_lat and surface_lon to WKT POINT(lon lat) for PostGIS
            if 'surface_lon' in df_wells.columns and 'surface_lat' in df_wells.columns:
                df_wells['surface_location'] = df_wells.apply(
                    lambda row: f"POINT({row['surface_lon']} {row['surface_lat']})", axis=1
                )
                
                # Drop original lat/lon columns as they are not explicitly defined in the SQLAlchemy model
                df_wells = df_wells.drop(columns=['surface_lat', 'surface_lon'])
            
            # Convert NaN to None for clean SQLAlchemy insertion
            df_wells = df_wells.replace({np.nan: None})
            
            # Bulk insert
            wells_records = cast(list[dict[str, Any]], df_wells.to_dict(orient='records'))
            session.bulk_insert_mappings(WellMaster, wells_records)
            session.commit()
            logger.info(f"Successfully inserted {len(wells_records)} rows into WellMaster.")
        else:
            logger.warning("wells_master.csv not found. Skipping.")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to ingest wells_master.csv: {e}")

    # Helper function for chunked bulk inserts
    def ingest_chunked(file_name, model_class):
        file_path = PROCESSED_DATA_DIR / file_name
        if not file_path.exists():
            logger.warning(f"{file_name} not found. Skipping.")
            return

        logger.info(f"Ingesting {file_name} in chunks...")
        total_rows = 0
        try:
            # Chunk reading to preserve memory on massive datasets
            for chunk in pd.read_csv(file_path, chunksize=10000):
                
                # Convert timestamp if parsing drilling params
                if file_name == "drilling_params.csv" and 'timestamp' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['timestamp'])
                
                # Replace NaNs with None so Postgres handles it as NULL rather than throwing Float 'NaN' errors
                chunk = chunk.replace({np.nan: None})
                
                records = cast(list[dict[str, Any]], chunk.to_dict(orient='records'))
                session.bulk_insert_mappings(model_class, records)
                session.commit()
                total_rows += len(records)
                logger.info(f"  Inserted {total_rows} rows so far into {model_class.__name__}...")
                
            logger.info(f"Successfully inserted a total of {total_rows} rows into {model_class.__name__}.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to ingest {file_name}: {e}")

    # 2. Ingest drilling_params.csv
    ingest_chunked("drilling_params.csv", DrillingParam)

    # 3. Ingest well_logs.csv
    ingest_chunked("well_logs.csv", WellLog)

    # 4. Ingest synthetic_events.csv
    ingest_chunked("synthetic_events.csv", SyntheticEvent)

    session.close()
    logger.info("Database seeding process completed.")

if __name__ == "__main__":
    seed_database()
