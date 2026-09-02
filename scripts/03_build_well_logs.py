import os
import pandas as pd
import numpy as np
import lasio
from pathlib import Path
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, COLUMN_ALIASES, logger

def normalize_columns(df):
    col_map = {col: col for col in df.columns}
    for col in df.columns:
        upper_col = col.upper()
        if upper_col in COLUMN_ALIASES:
            col_map[col] = COLUMN_ALIASES[upper_col]
        elif 'RES' in upper_col or 'ILD' in upper_col:
            col_map[col] = 'resistivity'
        elif 'SON' in upper_col or 'DT' in upper_col:
            col_map[col] = 'sonic'
        elif 'DEN' in upper_col or 'RHOB' in upper_col or 'PE' in upper_col:
            col_map[col] = 'density'
    return df.rename(columns=col_map)

def assign_formation(depth):
    # Simulated geological formation tops for Assam-Arakan basin
    if pd.isna(depth):
        return "Unknown"
    elif depth < 1500:
        return "Tipam"
    elif 1500 <= depth < 2500:
        return "Barail"
    else:
        return "Kopili"

def build_well_logs():
    logger.info("Building well logs...")
    
    schema = ['well_id', 'depth_tvd', 'gamma_ray', 'resistivity', 'sonic', 'density', 'formation']
    all_data = []

    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            file_path = Path(root) / file
            if file.endswith('.las'):
                try:
                    las = lasio.read(str(file_path))
                    df = las.df().reset_index()
                    df = normalize_columns(df)
                    
                    well_id = las.well.WELL.value if hasattr(las.well, 'WELL') and las.well.WELL.value else file_path.stem
                    if not str(well_id).startswith("OIL-"):
                        well_id = f"OIL-{str(well_id).upper()}"
                    df['well_id'] = well_id
                    all_data.append(df)
                except Exception as e:
                    logger.warning(f"Error reading LAS file {file}: {e}")
            elif file.endswith('.csv') and 'facies' in file.lower():
                try:
                    df = pd.read_csv(file_path)
                    df = normalize_columns(df)
                    if 'well_id' not in df.columns and 'well name' in df.columns.str.lower():
                        well_col = [c for c in df.columns if 'well name' in c.lower()][0]
                        df['well_id'] = df[well_col].apply(lambda x: f"OIL-{str(x).upper()}" if not str(x).startswith("OIL-") else x)
                    elif 'well_id' not in df.columns:
                        df['well_id'] = f"OIL-{file_path.stem.upper()}"
                    all_data.append(df)
                except Exception as e:
                    logger.warning(f"Error reading CSV file {file}: {e}")

    if not all_data:
        logger.info("No raw well logs found. Generating synthetic well log data...")
        wells_master_path = PROCESSED_DATA_DIR / "wells_master.csv"
        if wells_master_path.exists():
            df_wells = pd.read_csv(wells_master_path)
            well_ids = df_wells['well_id'].unique().tolist()
        else:
            well_ids = ["OIL-BAGHJAN-1", "OIL-NAHARKATIYA-1", "OIL-MORAN-1"]
            
        synthetic_rows = []
        for w_idx, wid in enumerate(well_ids):
            # Create a geological shift for each well (0 for first well, varying for others)
            structural_shift = w_idx * 150 + (np.random.randint(-50, 50) if w_idx > 0 else 0)
            
            # Generate 150 depth points for each well to make the log viewer look realistic
            for i in range(150):
                base_depth = 1400 + i * 10
                actual_depth = base_depth + structural_shift
                
                # Synthetic geological signature using sine waves
                gr_base = 75 + 25 * np.sin(i / 15.0) + 15 * np.sin(i / 4.0)
                
                synthetic_rows.append({
                    'well_id': wid,
                    'depth_tvd': actual_depth,
                    'gamma_ray': gr_base + np.random.normal(0, 2), # Add small noise
                    'resistivity': 0.66 - i*0.002,
                    'sonic': 110.2 - i*0.2,
                    'density': 2.4 + i*0.002
                })
        df = pd.DataFrame(synthetic_rows)
    else:
        df = pd.concat(all_data, ignore_index=True)

    for col in schema:
        if col not in df.columns and col != 'formation':
            df[col] = np.nan
            
    df['formation'] = df['depth_tvd'].apply(assign_formation)
    
    df = df[schema]
    output_path = PROCESSED_DATA_DIR / "well_logs.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully generated {output_path} with {len(df)} records.")

if __name__ == "__main__":
    build_well_logs()
