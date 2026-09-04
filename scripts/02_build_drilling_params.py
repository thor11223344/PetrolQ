import os
import math
import pandas as pd
import numpy as np
from pathlib import Path
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, COLUMN_ALIASES, logger

def normalize_columns(df):
    col_map = {col: col for col in df.columns}
    for col in df.columns:
        upper_col = col.upper()
        if upper_col in COLUMN_ALIASES:
            col_map[col] = COLUMN_ALIASES[upper_col]
        else:
            col_map[col] = col.lower()
    return df.rename(columns=col_map)

def build_drilling_params():
    logger.info("Building drilling parameters...")
    schema = ['well_id', 'timestamp', 'depth_md', 'depth_tvd', 'rop', 'wob', 'rpm', 'torque', 'mud_weight', 'ecd', 'mse', 'd_xc']
    
    all_data = []
    
    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            if file.endswith('.csv') and 'drill' in file.lower():
                file_path = Path(root) / file
                try:
                    df = pd.read_csv(file_path)
                    df = normalize_columns(df)
                    
                    for col in schema:
                        if col not in df.columns and col not in ['mse', 'd_xc']:
                            df[col] = np.nan
                            
                    if df['well_id'].isna().all():
                        df['well_id'] = "OIL-VOLVE-15-9-F-14"
                        
                    all_data.append(df)
                except Exception as e:
                    logger.warning(f"Error parsing {file_path}: {e}")

    if not all_data:
        logger.info("No raw drilling data found. Generating synthetic data for pipeline validation...")
        wells_master_path = PROCESSED_DATA_DIR / "wells_master.csv"
        if wells_master_path.exists():
            df_wells = pd.read_csv(wells_master_path)
            well_ids = df_wells['well_id'].unique().tolist()
        else:
            well_ids = ["OIL-BAGHJAN-1"]
            
        synthetic_rows = []
        for wid in well_ids:
            for i in range(5):
                synthetic_rows.append({
                    'well_id': wid,
                    'timestamp': pd.Timestamp("2024-01-01") + pd.Timedelta(minutes=i),
                    'depth_md': 2870 + i*10,
                    'depth_tvd': 2850 + i*10,
                    'rop': 22.9 - i*0.8,
                    'wob': 15.4 + i*0.1,
                    'rpm': 84 - i,
                    'torque': (21.3 + i*0.5) * 1000.0,  # Converted from kft-lbf to ft-lbf (consistent with service.py & simulator.py)
                    'mud_weight': 1.17,
                    'ecd': 1.2 + i*0.01
                })
        df = pd.DataFrame(synthetic_rows)
    else:
        df = pd.concat(all_data, ignore_index=True)
        # If raw torque is in kft-lbf / kN-m scale (e.g. max < 100), convert to ft-lbf
        if 'torque' in df.columns and pd.to_numeric(df['torque'], errors='coerce').max() < 100.0:
            df['torque'] = df['torque'] * 1000.0

    # Calculate MSE (exact match with calculate_mse() in backend/ml/service.py:
    # Teale 1965 + Dupriest & Koederitz 2005 mechanical efficiency eta = 0.35)
    bit_diameter = 8.5
    A_b = (math.pi / 4.0) * (bit_diameter ** 2)
    safe_rop = df['rop'].replace(0, np.nan)
    wob_lbf = df['wob'] * 1000.0                        # klbf -> lbf
    rop_ft_hr = safe_rop * 3.28084                      # m/hr -> ft/hr
    axial_psi = wob_lbf / A_b
    rotary_psi = (120.0 * math.pi * df['rpm'] * df['torque']) / (A_b * rop_ft_hr)
    eta = 0.35                                          # Drill bit mechanical efficiency factor
    total_mse_psi = axial_psi + (rotary_psi / eta)
    df['mse'] = (total_mse_psi / 1000.0).round(2)       # psi -> kpsi
    df.loc[df['rop'] <= 0.05, 'mse'] = 115.0            # Stalling limit matching service.py

    # Calculate Corrected d-exponent (d_xc)
    safe_rpm = df['rpm'].replace(0, np.nan)
    safe_wob = df['wob'].replace(0, np.nan)
    safe_ecd = df['ecd'].replace(0, np.nan)
    
    # Standard field d-exponent expects WOB in lbs and ROP in ft/hr
    wob_lbs = safe_wob * 1000.0
    safe_rop_ft_hr = safe_rop * 3.28084
    
    # Applying absolute to avoid log of negative numbers due to bad data
    term1_val = (safe_rop_ft_hr / (60.0 * safe_rpm)).abs().replace(0, np.nan)
    term2_val = ((12.0 * wob_lbs) / (10**6 * bit_diameter)).abs().replace(0, np.nan)
    
    term1 = np.log10(term1_val.astype(float))
    term2 = np.log10(term2_val.astype(float))
    
    d_exponent = term1 / term2
    
    NORMAL_PRESSURE_GRADIENT = 9.0 # ppg
    df['d_xc'] = (d_exponent * (NORMAL_PRESSURE_GRADIENT / safe_ecd)).round(3)

    # Clean missing values replacing with pd.NA or similar for csv
    df = df[schema]
    
    output_path = PROCESSED_DATA_DIR / "drilling_params.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully generated {output_path} with {len(df)} records.")

if __name__ == "__main__":
    build_drilling_params()
