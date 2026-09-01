import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
from config import PROCESSED_DATA_DIR, logger

# Define scripts to run in sequence
SCRIPTS = [
    "01_build_wells_master.py",
    "02_build_drilling_params.py",
    "03_build_well_logs.py",
    "04_build_events.py"
]

def run_scripts():
    logger.info("Starting Master Pipeline Runner...")
    script_dir = Path(__file__).resolve().parent
    
    for script_name in SCRIPTS:
        script_path = script_dir / script_name
        logger.info(f"Executing {script_name}...")
        try:
            # Use sys.executable to ensure we use the same Python interpreter
            result = subprocess.run([sys.executable, str(script_path)], check=True, text=True, capture_output=True)
            if result.stdout:
                logger.info(f"{script_name} stdout:\n{result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute {script_name}")
            logger.error(f"Error Output:\n{e.stderr}")
            sys.exit(1)

def validate_and_summarize():
    logger.info("Starting post-run validation checks...")
    
    # Define files and their critical columns
    files = {
        "wells_master.csv": {
            "primary_keys": ["well_id"],
            "depth_cols": ["total_depth_tvd"]
        },
        "drilling_params.csv": {
            "primary_keys": ["well_id", "timestamp"],
            "depth_cols": ["depth_md", "depth_tvd"]
        },
        "well_logs.csv": {
            "primary_keys": ["well_id"],
            "depth_cols": ["depth_tvd"]
        },
        "synthetic_events.csv": {
            "primary_keys": ["event_id", "well_id"],
            "depth_cols": ["depth_start_tvd", "depth_end_tvd"]
        }
    }
    
    master_wells = set()
    summary_data = []

    # 1. Existence and non-empty check
    for file_name, meta in files.items():
        file_path = PROCESSED_DATA_DIR / file_name
        
        if not file_path.exists():
            logger.error(f"Validation Failed: {file_name} does not exist.")
            sys.exit(1)
            
        file_size_kb = file_path.stat().st_size / 1024
        
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Validation Failed: Could not read {file_name}. Error: {e}")
            sys.exit(1)
            
        if df.empty:
            logger.error(f"Validation Failed: {file_name} is empty.")
            sys.exit(1)

        # 2. Extract master well IDs for referential integrity
        if file_name == "wells_master.csv":
            master_wells = set(df['well_id'].unique())
        else:
            # 3. Referential integrity check
            file_wells = set(df['well_id'].unique())
            missing_wells = file_wells - master_wells
            if missing_wells:
                logger.error(f"Validation Failed: {file_name} contains well_ids not in wells_master.csv: {missing_wells}")
                sys.exit(1)

        # 4. Check for unhandled NaNs in primary keys and depth columns
        cols_to_check = meta["primary_keys"] + meta["depth_cols"]
        for col in cols_to_check:
            if col in df.columns:
                if df[col].isna().any():
                    nan_count = df[col].isna().sum()
                    logger.error(f"Validation Failed: {file_name} contains {nan_count} NaN values in critical column '{col}'")
                    sys.exit(1)
            else:
                logger.error(f"Validation Failed: {file_name} is missing critical column '{col}'")
                sys.exit(1)
                
        # Collect summary metrics
        unique_wells = df['well_id'].nunique() if 'well_id' in df.columns else 0
        summary_data.append({
            "Dataset": file_name,
            "Rows": len(df),
            "Unique Wells": unique_wells,
            "File Size (KB)": f"{file_size_kb:.2f}"
        })
        
    logger.info("Validation passed successfully. All checks cleared.")
    
    # 5. Print summary table
    print("\n" + "="*80)
    print(f"{'Data Pipeline Execution Summary':^80}")
    print("="*80)
    print(f"{'Dataset':<25} | {'Row Count':<12} | {'Unique Wells':<15} | {'File Size (KB)':<15}")
    print("-" * 80)
    for row in summary_data:
        print(f"{row['Dataset']:<25} | {row['Rows']:<12} | {row['Unique Wells']:<15} | {row['File Size (KB)']:<15}")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_scripts()
    validate_and_summarize()
