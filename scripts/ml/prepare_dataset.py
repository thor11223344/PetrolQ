import os
import pandas as pd
import numpy as np

def prepare_ml_dataset(params_path, events_path, output_path):
    print(f"Loading datasets from {params_path} and {events_path}...")
    
    try:
        df_params = pd.read_csv(params_path)
        df_events = pd.read_csv(events_path)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # Check for required columns
    required_cols = ['well_id', 'depth_tvd', 'rop', 'torque', 'mud_weight']
    missing_cols = [c for c in required_cols if c not in df_params.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols}")
        
    print("Engineering rolling features...")
    # Sort to ensure sequential depth order for rolling calculations
    df_params = df_params.sort_values(by=['well_id', 'depth_tvd']).reset_index(drop=True)
    
    # 1. Rolling variations (5-point rolling mean and std)
    rolling_cols = ['rop', 'torque', 'mud_weight']
    for col in rolling_cols:
        if col in df_params.columns:
            df_params[f'{col}_roll_mean_5'] = df_params.groupby('well_id')[col].transform(lambda x: x.rolling(5, min_periods=1).mean())
            df_params[f'{col}_roll_std_5'] = df_params.groupby('well_id')[col].transform(lambda x: x.rolling(5, min_periods=1).std())
            
    # Ensure mse and d_xc exist
    if 'mse' not in df_params.columns:
        print("Warning: mse not found, inserting dummy 0.0 values.")
        df_params['mse'] = 0.0
    if 'd_xc' not in df_params.columns:
        print("Warning: d_xc not found, inserting dummy 0.0 values.")
        df_params['d_xc'] = 0.0
        
    # Ensure physical well-control indicators exist
    if 'flow_out_pct' not in df_params.columns:
        df_params['flow_out_pct'] = 100.0
    if 'pit_gain_bbl' not in df_params.columns:
        df_params['pit_gain_bbl'] = 0.0
    if 'spp_psi' not in df_params.columns:
        df_params['spp_psi'] = 2800.0

    # Fill NaN for rolling std where window < 2
    df_params = df_params.fillna({
        'flow_out_pct': 100.0,
        'pit_gain_bbl': 0.0,
        'spp_psi': 2800.0
    }).fillna(0.0)

    print("Generating target labels (30m look-ahead window)...")
    # 2. Target Labeling
    df_params['hazard_upcoming'] = 0
    df_params['hazard_type'] = 'Normal'

    # Iterate through synthetic events to label the preceding 30 meters
    for _, event in df_events.iterrows():
        well = event.get('well_id')
        incident_depth = event.get('depth_start_tvd')
        
        if incident_depth is None or pd.isna(incident_depth):
            continue
            
        event_type = str(event.get('event_type', 'Unknown'))
        
        # Mask for the well and within 30m above the incident depth
        mask = (
            (df_params['well_id'] == well) & 
            (df_params['depth_tvd'] >= incident_depth - 30.0) & 
            (df_params['depth_tvd'] <= incident_depth)
        )

        df_params.loc[mask, 'hazard_upcoming'] = 1
        
        # Map to multi-class hazard type
        event_lower = event_type.lower()
        if 'stuck' in event_lower:
            hazard_class = 'Stuck Pipe'
        elif 'kick' in event_lower or 'gas' in event_lower:
            hazard_class = 'Gas Kick'
        elif 'loss' in event_lower or 'lost' in event_lower:
            hazard_class = 'Lost Circulation'
        else:
            hazard_class = event_type
            
        df_params.loc[mask, 'hazard_type'] = hazard_class
        
    print("Cleaning dataset...")
    df_params.dropna(inplace=True)

    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_params.to_csv(output_path, index=False)
    
    print(f"Successfully generated ML training dataset at: {output_path}")
    print(f"Total Rows: {len(df_params)}")
    print(f"\nHazard Distribution:\n{df_params['hazard_type'].value_counts()}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    params_path = os.path.join(base_dir, 'data', 'processed', 'drilling_params.csv')
    events_path = os.path.join(base_dir, 'data', 'processed', 'synthetic_events.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'ml_training_data.csv')
    
    prepare_ml_dataset(params_path, events_path, output_path)
