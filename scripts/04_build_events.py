import os
import pandas as pd
import random
from pathlib import Path
from config import PROCESSED_DATA_DIR, logger

def build_events():
    logger.info("Building historical incidents (events)...")
    schema = ['event_id', 'well_id', 'depth_start_tvd', 'depth_end_tvd', 'formation', 'event_type', 'severity', 'root_cause', 'mitigation_applied', 'npt_hours']
    
    wells_master_path = PROCESSED_DATA_DIR / "wells_master.csv"
    if wells_master_path.exists():
        df_wells = pd.read_csv(wells_master_path)
        well_ids = df_wells['well_id'].unique().tolist()
    else:
        logger.warning(f"{wells_master_path} not found. Using default mock wells.")
        well_ids = ["OIL-BAGHJAN-1", "OIL-NAHARKATIYA-1"]

    events = []
    
    event_types = ['Lost Circulation', 'Kick', 'Stuck Pipe', 'Equipment Failure', 'Wellbore Instability']
    severities = ['Low', 'Medium', 'High', 'Critical']
    
    # Set seed for reproducibility in mock generation
    random.seed(42)
    event_counter = 1
    
    for well_id in well_ids:
        num_events = random.randint(1, 3)
        for _ in range(num_events):
            event_type = random.choice(event_types)
            depth_start = random.uniform(1000, 3500)
            depth_end = depth_start + random.uniform(10, 100)
            
            if depth_start < 1500:
                formation = "Tipam"
            elif 1500 <= depth_start < 2500:
                formation = "Barail"
            else:
                formation = "Kopili"
                
            events.append({
                'event_id': f"EVT-{event_counter:04d}",
                'well_id': well_id,
                'depth_start_tvd': round(depth_start, 2),
                'depth_end_tvd': round(depth_end, 2),
                'formation': formation,
                'event_type': event_type,
                'severity': random.choice(severities),
                'root_cause': f"Synthetic cause for {event_type}",
                'mitigation_applied': f"Standard mitigation for {event_type}",
                'npt_hours': round(random.uniform(1.0, 48.0), 1)
            })
            event_counter += 1

    df_events = pd.DataFrame(events, columns=schema)
    output_path = PROCESSED_DATA_DIR / "synthetic_events.csv"
    df_events.to_csv(output_path, index=False)
    logger.info(f"Successfully generated {output_path} with {len(df_events)} events.")

if __name__ == "__main__":
    build_events()
