import asyncio
import websockets
import json
import pandas as pd
import os

async def simulate_live_feed():
    uri = "ws://localhost:8000/api/ws/telemetry"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'processed', 'drilling_params.csv')
    
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}. Please run previous data generation scripts.")
        return
        
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Use the available depth range
    if 'depth_tvd' in df.columns:
        min_depth = df['depth_tvd'].min()
        max_depth = df['depth_tvd'].max()
        anomaly_depth = min_depth + (max_depth - min_depth) / 2
        
        df = df[(df['depth_tvd'] >= min_depth) & (df['depth_tvd'] <= max_depth)].copy()
        df.sort_values(by='depth_tvd', inplace=True)
    
    if len(df) == 0:
        print("No data found in the dataset.")
        return
        
    print(f"Connecting to RTMS WebSocket at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully. Starting telemetry feed...\n")
            
            while True:
                for _, row in df.iterrows():
                    depth = float(row.get('depth_tvd', 2000.0))
                    rop = float(row.get('rop', 15.0))
                    wob = float(row.get('wob', 10.0))
                    rpm = float(row.get('rpm', 120.0))
                    torque = float(row.get('torque', 15000.0))
                    mud_weight = float(row.get('mud_weight', 10.5))
                    
                    # Inject hazard anomaly
                    if depth >= anomaly_depth:
                        torque = 28500.0  # Spike torque massively to guarantee alert
                        rop *= 0.5      # Drop ROP by half
                        depth = 2450.0  # Match the exact depth trained for anomaly
                        mud_weight = 11.8 # Match the exact mud weight trained for anomaly
                        print(f"[ANOMALY INJECTED] Triggering exact condition: Depth={depth}m, Torque={torque}")

                    payload = {
                        "depth_tvd": depth,
                        "rop": rop,
                        "wob": wob,
                        "rpm": rpm,
                        "torque": torque,
                        "mud_weight": mud_weight
                    }
                    
                    print(f"Sending : {payload}")
                    await websocket.send(json.dumps(payload))
                    
                    # Receive response (prediction alert)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        res_data = json.loads(response)
                        prediction = res_data.get("prediction", {})
                        risk = prediction.get("risk_level", "UNKNOWN")
                        prob = prediction.get("risk_probability", 0.0)
                        
                        status_indicator = "OK" if risk == "LOW" else "WARN" if risk == "MEDIUM" else "CRITICAL"
                        print(f"Response: [{status_indicator}] Risk Level: {risk} (Probability: {prob:.2f})\n")
                    except asyncio.TimeoutError:
                        print("Response: Timeout waiting for server response.\n")
                    except Exception as e:
                        print(f"Response: Error - {e}\n")
                        
                    await asyncio.sleep(1.0)

                
    except ConnectionRefusedError:
        print(f"Connection refused to {uri}. Ensure the FastAPI server is running.")

if __name__ == "__main__":
    try:
        asyncio.run(simulate_live_feed())
    except KeyboardInterrupt:
        print("\nLive feed simulator stopped by user.")
