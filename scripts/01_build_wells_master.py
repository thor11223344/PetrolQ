import os
import pandas as pd
from pathlib import Path
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, logger

def rebrand_well_id(raw_id):
    raw_str = str(raw_id)
    if not raw_str.startswith("OIL-"):
        return f"OIL-{raw_str.upper()}"
    return raw_str.upper()

def build_wells_master():
    logger.info("Building wells master data...")
    schema = ['well_id', 'field_name', 'surface_lat', 'surface_lon', 'kb_elevation', 'total_depth_tvd', 'spud_date']
    
    all_wells = []
    
    # 1. Search for well metadata files in raw
    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            file_path = Path(root) / file
            if file.endswith('.json') and 'well' in file.lower():
                try:
                    df_raw = pd.read_json(file_path)
                    for _, row in df_raw.iterrows():
                        well_id = rebrand_well_id(row.get('well_id', row.get('wellName', 'UNKNOWN')))
                        lat = row.get('location', {}).get('latitude', 27.4) if isinstance(row.get('location'), dict) else row.get('latitude', 27.4)
                        lon = row.get('location', {}).get('longitude', 95.1) if isinstance(row.get('location'), dict) else row.get('longitude', 95.1)
                        td = row.get('total_depth_md_m', row.get('MD', 3500))
                        
                        all_wells.append({
                            'well_id': well_id,
                            'field_name': 'Assam-Arakan',
                            'surface_lat': lat,
                            'surface_lon': lon,
                            'kb_elevation': 35.0,
                            'total_depth_tvd': td,
                            'spud_date': "2024-01-01"
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse JSON well file {file}: {e}")
            elif file.endswith('.csv') and ('well' in file.lower() or 'survey' in file.lower()):
                try:
                    df_raw = pd.read_csv(file_path)
                    well_col = next((col for col in df_raw.columns if 'well' in col.lower()), None)
                    if well_col:
                        unique_wells = df_raw[well_col].dropna().unique()
                        for w in unique_wells:
                            all_wells.append({
                                'well_id': rebrand_well_id(w),
                                'field_name': 'Assam-Arakan',
                                'surface_lat': 27.412,
                                'surface_lon': 95.182,
                                'kb_elevation': 35.0,
                                'total_depth_tvd': 3500,
                                'spud_date': "2024-01-01"
                            })
                except Exception as e:
                    logger.warning(f"Failed to parse CSV well file {file}: {e}")

    df_out = pd.DataFrame(all_wells)
    
    # Fallback to synthetic if no raw data processed (for foundational setup)
    if df_out.empty:
        logger.info("No well data found in raw/. Supplying synthetic Volve defaults...")
        synthetic_data = [
            {"well_id": "OIL-VOLVE-15-9-F-14", "field_name": "Assam-Arakan", "surface_lat": 27.412, "surface_lon": 95.182, "kb_elevation": 35.0, "total_depth_tvd": 3520, "spud_date": "2024-01-10"},
            {"well_id": "OIL-VOLVE-15-9-F-15", "field_name": "Assam-Arakan", "surface_lat": 27.417, "surface_lon": 95.188, "kb_elevation": 34.5, "total_depth_tvd": 3490, "spud_date": "2024-02-15"}
        ]
        df_out = pd.DataFrame(synthetic_data)
    else:
        df_out = df_out.drop_duplicates(subset=['well_id'])

    df_out = df_out[schema]
    output_path = PROCESSED_DATA_DIR / "wells_master.csv"
    df_out.to_csv(output_path, index=False)
    logger.info(f"Successfully generated {output_path} with {len(df_out)} records.")

if __name__ == "__main__":
    build_wells_master()
