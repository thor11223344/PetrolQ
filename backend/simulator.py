import asyncio
import json
import random
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
from ml.service import HazardPredictionService

class WebSocketConnectionManager:
    """
    Centralized broadcaster for telemetry WebSocket connections.
    Synchronizes all connected browser clients with simultaneous updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket] Client connected. Total active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WebSocket] Client disconnected. Total active clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON-serializable message to all active WebSocket connections."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WebSocket] Broadcast error to client: {e}")
                disconnected.append(connection)
                
        for dead_conn in disconnected:
            self.disconnect(dead_conn)

ws_manager = WebSocketConnectionManager()

class TelemetrySimulator:
    """
    Singleton In-App Telemetry Simulator.
    Drives realistic underlying drilling parameters along well trajectory.
    When scenarios are injected, realistically mutates flow-out, pit volume, SPP,
    torque, ROP, and ECD according to physical drilling mechanics.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetrySimulator, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.well_id = "OIL-BAGHJAN-1"
        self.depth_tvd = 2240.0
        self.rop = 16.5
        self.wob = 14.0
        self.rpm = 105.0
        self.torque = 13200.0
        self.mud_weight = 11.2
        self.ecd = 11.6
        self.flow_out_pct = 100.0
        self.pit_gain_bbl = 0.0
        self.spp_psi = 2800.0
        
        self.is_running = False
        self.active_scenario = "normal"  # "normal" | "gas_kick" | "lost_circulation" | "stuck_pipe"
        self.history: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None
        self.ml_service = HazardPredictionService()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "active_scenario": self.active_scenario,
            "well_id": self.well_id,
            "current_params": self._get_current_params()
        }

    def _get_current_params(self) -> Dict[str, Any]:
        return {
            "well_id": self.well_id,
            "depth_tvd": round(self.depth_tvd, 2),
            "rop": round(self.rop, 2),
            "wob": round(self.wob, 2),
            "rpm": round(self.rpm, 1),
            "torque": round(self.torque, 1),
            "mud_weight": round(self.mud_weight, 2),
            "ecd": round(self.ecd, 2),
            "flow_out_pct": round(self.flow_out_pct, 1),
            "pit_gain_bbl": round(self.pit_gain_bbl, 1),
            "spp_psi": round(self.spp_psi, 1)
        }

    def set_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        CORRECTION 4 REQUIREMENT:
        Modifies underlying simulated telemetry values realistically for that scenario type.
        The ML/hazard-scoring pipeline computes the resulting risk score from those simulated values.
        Does NOT directly override or fake the risk score.
        """
        self.active_scenario = scenario.lower().strip()
        
        if self.active_scenario == "gas_kick":
            # Realistic gas influx signature:
            # - Formation fluid enters wellbore -> delta flow-out increases significantly
            # - Pit level rises (gain in active tanks)
            # - Lighter gas column in annulus reduces bottomhole hydrostatic and standpipe pressure
            # - Penetrating high-permeability sand -> drilling break (ROP spike)
            self.flow_out_pct = 118.5
            self.pit_gain_bbl = 15.2
            self.spp_psi = 2450.0
            self.rop = 24.5
            self.wob = 13.5
            self.torque = 14200.0
            self.ecd = 11.1
            
        elif self.active_scenario == "lost_circulation":
            # Realistic mud loss signature:
            # - Mud escapes into fractured vugular formation -> flow-out return rate drops
            # - Pit level decreases as mud volume is lost downhole
            # - Annulus level drops -> hydrostatic head and ECD decrease
            self.flow_out_pct = 66.0
            self.pit_gain_bbl = -22.5
            self.spp_psi = 2600.0
            self.ecd = 10.7
            self.rop = 14.0
            self.torque = 12600.0
            
        elif self.active_scenario == "stuck_pipe":
            # Realistic mechanical / packoff sticking signature:
            # - Reactive shale sloughing or keyseat grabs drill collars
            # - Surface torque spikes violently towards make-up / motor stall limits
            # - ROP drops to zero or near zero as drillstring cannot progress
            # - Rotary RPM stalls, standpipe pressure ramps up due to restricted annular flow
            self.torque = 29500.0
            self.rop = 0.3
            self.rpm = 25.0
            self.wob = 18.5
            self.spp_psi = 3350.0
            self.flow_out_pct = 97.0
            self.pit_gain_bbl = 0.0
            
        else:
            # "normal" drilling baseline
            self.active_scenario = "normal"
            self.flow_out_pct = 100.0
            self.pit_gain_bbl = 0.0
            self.spp_psi = 2800.0
            self.rop = 16.5
            self.wob = 14.0
            self.rpm = 105.0
            self.torque = 13200.0
            self.ecd = 11.6

        params = self._get_current_params()
        prediction = self.ml_service.predict_risk(params, self.history)
        
        return {
            "scenario": self.active_scenario,
            "data": params,
            "prediction": prediction
        }

    async def step_and_broadcast(self):
        """Advances telemetry by one time tick, predicts risk, and broadcasts to all clients."""
        # Realistic depth increment: ~0.5m to 0.8m per second during live demo
        if self.is_running:
            step_m = (self.rop / 3600.0) * 150.0  # Scaled for responsive real-time UI progression
            self.depth_tvd += step_m

            # Add natural small variations if normal
            if self.active_scenario == "normal":
                self.torque += random.uniform(-150.0, 150.0)
                self.torque = max(11000.0, min(15000.0, self.torque))
                self.rop += random.uniform(-0.4, 0.4)
                self.rop = max(10.0, min(22.0, self.rop))
                self.flow_out_pct += random.uniform(-0.3, 0.3)
                self.spp_psi += random.uniform(-15.0, 15.0)
            elif self.active_scenario == "gas_kick":
                # Continuing pit gain expansion
                self.pit_gain_bbl += 0.3
                self.flow_out_pct += random.uniform(-0.5, 0.8)
                self.flow_out_pct = max(105.0, min(135.0, self.flow_out_pct))
            elif self.active_scenario == "lost_circulation":
                # Continuing pit loss
                self.pit_gain_bbl -= 0.4
                self.flow_out_pct += random.uniform(-0.8, 0.5)
                self.flow_out_pct = max(40.0, min(85.0, self.flow_out_pct))
            elif self.active_scenario == "stuck_pipe":
                self.torque += random.uniform(-200.0, 300.0)
                self.torque = max(26000.0, min(34000.0, self.torque))

        params = self._get_current_params()
        
        # Maintain history for rolling statistical metrics
        self.history.append(params)
        if len(self.history) > 20:
            self.history.pop(0)

        # Predict risk through unified ML & physics engine
        prediction = self.ml_service.predict_risk(params, self.history)

        payload = {
            "status": "success",
            "data": params,
            "prediction": prediction,
            "scenario": self.active_scenario,
            "is_running": self.is_running
        }

        # Centralized broadcast to all WebSocket clients (tabs)
        await ws_manager.broadcast(payload)
        return payload

    async def _run_loop(self):
        """Continuous background tick loop."""
        while self.is_running:
            try:
                await self.step_and_broadcast()
            except Exception as e:
                print(f"[Simulator] Error in simulation loop: {e}")
            await asyncio.sleep(1.0)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run_loop())
            print(f"[Simulator] Started telemetry feed for {self.well_id} at {self.depth_tvd:.1f}m TVD")

    def pause(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        print(f"[Simulator] Paused telemetry feed at {self.depth_tvd:.1f}m TVD")

    def reset(self, well_id: str = "OIL-BAGHJAN-1", depth_tvd: float = None):
        self.well_id = well_id
        WELL_DEPTHS = {
            'OIL-BAGHJAN-1': 2240.0,
            'OIL-BAGHJAN-4': 2380.0,
            'OIL-NAHARKATIYA-1': 2020.0,
            'OIL-MORAN-1': 2550.0,
            'OIL-DIKOM-1': 2200.0,
            'OIL-TENGAKHAT-1': 2100.0,
            'OIL-KOTHALONI-1': 2300.0,
            'OIL-HAPJAN-1': 2340.0,
            'OIL-SHALMARI-1': 2190.0,
        }
        self.depth_tvd = depth_tvd if depth_tvd is not None else WELL_DEPTHS.get(well_id, 2240.0)
        self.set_scenario("normal")
        print(f"[Simulator] Reset telemetry to {well_id} at {self.depth_tvd}m TVD")

telemetry_simulator = TelemetrySimulator()
