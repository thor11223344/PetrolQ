import os
import json
import logging
import pandas as pd
import lasio
from pathlib import Path

# Import configuration
from config import RAW_DATA_DIR, LOGS_DIR, logger

def inspect_files():
    logger.info("Starting inspection of raw data directory...")
    inspection_report = []

    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory does not exist: {RAW_DATA_DIR}")
        return

    # Walk through the raw data directory
    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            file_path = Path(root) / file
            file_ext = file_path.suffix.lower()
            
            # Initialize info dictionary
            file_info = {
                "file_name": file,
                "file_path": str(file_path.relative_to(RAW_DATA_DIR)),
                "extension": file_ext,
                "row_count": 0,
                "columns": [],
                "status": "success",
                "error": None
            }

            if file_ext not in ['.csv', '.xlsx', '.las']:
                continue

            logger.info(f"Inspecting file: {file_info['file_path']}")

            try:
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                    file_info["row_count"] = len(df)
                    file_info["columns"] = df.columns.tolist()

                elif file_ext == '.xlsx':
                    df = pd.read_excel(file_path)
                    file_info["row_count"] = len(df)
                    file_info["columns"] = df.columns.tolist()

                elif file_ext == '.las':
                    # Read LAS file
                    las = lasio.read(str(file_path))
                    df = las.df()
                    file_info["row_count"] = len(df)
                    
                    # Get columns, and prepend index name (usually DEPT) if available
                    cols = df.columns.tolist()
                    if df.index.name:
                        cols.insert(0, df.index.name)
                    file_info["columns"] = cols

                logger.info(f"Successfully read {file}: {file_info['row_count']} rows, {len(file_info['columns'])} columns.")

            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                file_info["status"] = "error"
                file_info["error"] = str(e)

            inspection_report.append(file_info)

    # Save the report to JSON
    report_path = LOGS_DIR / "inspection_summary.json"
    with open(report_path, "w") as f:
        json.dump(inspection_report, f, indent=4)
    
    logger.info(f"Inspection complete. Summary saved to: {report_path}")

if __name__ == "__main__":
    inspect_files()
