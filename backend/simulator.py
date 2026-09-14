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

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON-serializable message to all active WebSocket connections."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
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

WELL_CALIBRATED_BASELINES: Dict[str, Dict[str, Any]] = {
    # Upper Assam Shelf
    'OIL-BAGHJAN-1': {'depth_tvd': 2240.0, 'rop': 16.5, 'wob': 14.0, 'rpm': 105.0, 'torque': 13200.0, 'mud_weight': 11.2, 'ecd': 11.6, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2800.0},
    'OIL-BAGHJAN-4': {'depth_tvd': 2380.0, 'rop': 18.2, 'wob': 15.0, 'rpm': 110.0, 'torque': 14100.0, 'mud_weight': 11.4, 'ecd': 11.8, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2950.0},
    'OIL-NAHARKATIYA-1': {'depth_tvd': 2020.0, 'rop': 14.0, 'wob': 12.5, 'rpm': 95.0, 'torque': 11800.0, 'mud_weight': 10.8, 'ecd': 11.2, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2600.0},
    'OIL-MORAN-1': {'depth_tvd': 2550.0, 'rop': 15.0, 'wob': 13.0, 'rpm': 100.0, 'torque': 12500.0, 'mud_weight': 11.0, 'ecd': 11.4, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2750.0},
    'OIL-DIKOM-1': {'depth_tvd': 2200.0, 'rop': 17.0, 'wob': 14.5, 'rpm': 105.0, 'torque': 13500.0, 'mud_weight': 11.3, 'ecd': 11.7, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2850.0},
    'OIL-TENGAKHAT-1': {'depth_tvd': 2100.0, 'rop': 16.0, 'wob': 13.5, 'rpm': 100.0, 'torque': 12800.0, 'mud_weight': 11.1, 'ecd': 11.5, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2700.0},
    'OIL-KOTHALONI-1': {'depth_tvd': 2300.0, 'rop': 15.5, 'wob': 14.0, 'rpm': 105.0, 'torque': 13000.0, 'mud_weight': 11.2, 'ecd': 11.6, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2800.0},
    'OIL-HAPJAN-1': {'depth_tvd': 2400.0, 'rop': 14.5, 'wob': 13.0, 'rpm': 100.0, 'torque': 12500.0, 'mud_weight': 11.0, 'ecd': 11.4, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2750.0},
    'OIL-SHALMARI-1': {'depth_tvd': 2150.0, 'rop': 17.5, 'wob': 14.5, 'rpm': 110.0, 'torque': 13500.0, 'mud_weight': 11.3, 'ecd': 11.7, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2850.0},
    'OIL-KUSIJAN-1': {'depth_tvd': 2280.0, 'rop': 16.0, 'wob': 14.0, 'rpm': 102.0, 'torque': 13100.0, 'mud_weight': 11.1, 'ecd': 11.5, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2780.0},
    'OIL-HEBEDA-1': {'depth_tvd': 2220.0, 'rop': 16.2, 'wob': 13.8, 'rpm': 104.0, 'torque': 12900.0, 'mud_weight': 11.0, 'ecd': 11.4, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2760.0},

    # Rajasthan Basin (Barmer/Jaisalmer)
    'OIL-RAJ-BAGHEWALA-1': {'depth_tvd': 2100.0, 'rop': 10.5, 'wob': 12.0, 'rpm': 90.0, 'torque': 14500.0, 'mud_weight': 10.5, 'ecd': 11.0, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2100.0},
    'OIL-RAJ-BAGHEWALA-2': {'depth_tvd': 2150.0, 'rop': 11.0, 'wob': 12.5, 'rpm': 92.0, 'torque': 14800.0, 'mud_weight': 10.6, 'ecd': 11.1, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2150.0},
    'OIL-RAJ-TANOT-1': {'depth_tvd': 1950.0, 'rop': 11.2, 'wob': 13.0, 'rpm': 95.0, 'torque': 14200.0, 'mud_weight': 10.4, 'ecd': 10.9, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2050.0},
    'OIL-RAJ-TANOT-2': {'depth_tvd': 2000.0, 'rop': 11.5, 'wob': 13.2, 'rpm': 96.0, 'torque': 14300.0, 'mud_weight': 10.5, 'ecd': 11.0, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2080.0},
    'OIL-RAJ-DANDEWALA-1': {'depth_tvd': 2050.0, 'rop': 10.8, 'wob': 12.8, 'rpm': 94.0, 'torque': 14400.0, 'mud_weight': 10.4, 'ecd': 10.9, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 2060.0},

    # KG Deepwater (Krishna-Godavari)
    'OIL-KG-DEEPWATER-1': {'depth_tvd': 3200.0, 'rop': 8.5, 'wob': 18.0, 'rpm': 85.0, 'torque': 18500.0, 'mud_weight': 13.2, 'ecd': 13.8, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 4100.0},
    'OIL-KG-DWN-98-2': {'depth_tvd': 3350.0, 'rop': 8.2, 'wob': 18.5, 'rpm': 82.0, 'torque': 19100.0, 'mud_weight': 13.4, 'ecd': 14.0, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 4250.0},
    'OIL-KG-D6-OFFSHORE': {'depth_tvd': 3450.0, 'rop': 7.8, 'wob': 19.0, 'rpm': 80.0, 'torque': 19800.0, 'mud_weight': 13.6, 'ecd': 14.2, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 4400.0},
    'OIL-KG-YANAM-1': {'depth_tvd': 2950.0, 'rop': 9.5, 'wob': 16.5, 'rpm': 90.0, 'torque': 17200.0, 'mud_weight': 12.8, 'ecd': 13.3, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 3850.0},
    'OIL-KG-AMALAPURAM-1': {'depth_tvd': 2850.0, 'rop': 10.2, 'wob': 16.0, 'rpm': 92.0, 'torque': 16800.0, 'mud_weight': 12.5, 'ecd': 13.0, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 3700.0},

    # Mizoram Fold Belt
    'OIL-MZ-AIZAWL-1': {'depth_tvd': 2800.0, 'rop': 7.5, 'wob': 22.0, 'rpm': 80.0, 'torque': 21500.0, 'mud_weight': 12.5, 'ecd': 13.0, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 3800.0},
    'OIL-MZ-MAMIT-1': {'depth_tvd': 2920.0, 'rop': 7.2, 'wob': 22.5, 'rpm': 78.0, 'torque': 22100.0, 'mud_weight': 12.7, 'ecd': 13.2, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 3950.0},
    'OIL-MZ-KOLASIB-1': {'depth_tvd': 2750.0, 'rop': 7.8, 'wob': 21.5, 'rpm': 82.0, 'torque': 20900.0, 'mud_weight': 12.4, 'ecd': 12.9, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 3750.0},
    'OIL-MZ-LUNGLEI-1': {'depth_tvd': 3100.0, 'rop': 6.8, 'wob': 23.0, 'rpm': 75.0, 'torque': 22800.0, 'mud_weight': 12.9, 'ecd': 13.5, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 4100.0},
    'OIL-MZ-CHAMPHAI-1': {'depth_tvd': 3250.0, 'rop': 6.5, 'wob': 23.5, 'rpm': 72.0, 'torque': 23400.0, 'mud_weight': 13.1, 'ecd': 13.7, 'flow_out_pct': 100.0, 'pit_gain_bbl': 0.0, 'spp_psi': 4250.0},
}

def get_well_region_tag(well_id: str) -> str:
    wid = (well_id or "").upper()
    if "RAJ" in wid: return "rajasthan"
    if "KG" in wid: return "kg"
    if "MZ" in wid or "MIZO" in wid: return "mizoram"
    return "assam"

def get_well_calibrated_baseline(well_id: str) -> Dict[str, Any]:
    if well_id in WELL_CALIBRATED_BASELINES:
        return dict(WELL_CALIBRATED_BASELINES[well_id])
    # Match by region fallback
    reg = get_well_region_tag(well_id)
    if reg == "rajasthan":
        return dict(WELL_CALIBRATED_BASELINES['OIL-RAJ-BAGHEWALA-1'])
    elif reg == "kg":
        return dict(WELL_CALIBRATED_BASELINES['OIL-KG-DEEPWATER-1'])
    elif reg == "mizoram":
        return dict(WELL_CALIBRATED_BASELINES['OIL-MZ-AIZAWL-1'])
    return dict(WELL_CALIBRATED_BASELINES['OIL-BAGHJAN-1'])

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
        base = get_well_calibrated_baseline(self.well_id)
        self.depth_tvd = base['depth_tvd']
        self.rop = base['rop']
        self.wob = base['wob']
        self.rpm = base['rpm']
        self.torque = base['torque']
        self.mud_weight = base['mud_weight']
        self.ecd = base['ecd']
        self.flow_out_pct = base['flow_out_pct']
        self.pit_gain_bbl = base['pit_gain_bbl']
        self.spp_psi = base['spp_psi']
        
        self.is_running = False
        self.speed_multiplier = 1.0
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
        base = get_well_calibrated_baseline(self.well_id)
        reg = get_well_region_tag(self.well_id)
        
        if self.active_scenario == "gas_kick":
            # Realistic gas influx signature:
            # - Formation fluid enters wellbore -> delta flow-out increases significantly
            # - Pit level rises (gain in active tanks)
            # - Lighter gas column in annulus reduces bottomhole hydrostatic and standpipe pressure
            # - Penetrating high-permeability sand -> drilling break (ROP spike)
            self.flow_out_pct = 126.0 if reg == "kg" else 118.5
            self.pit_gain_bbl = 20.0 if reg == "kg" else 15.2
            self.spp_psi = max(1800.0, base['spp_psi'] - 350.0)
            self.rop = base['rop'] * 1.6
            self.wob = max(10.0, base['wob'] - 1.0)
            self.torque = base['torque'] * 1.08
            self.ecd = base['ecd'] - 0.5
            
        elif self.active_scenario == "lost_circulation":
            # Realistic mud loss signature:
            # - Mud escapes into fractured vugular formation -> flow-out return rate drops
            # - Pit level decreases as mud volume is lost downhole
            # - Annulus level drops -> hydrostatic head and ECD decrease
            self.flow_out_pct = 48.0 if reg == "rajasthan" else 66.0
            self.pit_gain_bbl = -32.0 if reg == "rajasthan" else -22.5
            self.spp_psi = max(1500.0, base['spp_psi'] - 300.0)
            self.ecd = base['ecd'] - 0.8
            self.rop = base['rop'] * 0.9
            self.torque = base['torque'] * 0.95
            
        elif self.active_scenario == "stuck_pipe":
            # Realistic mechanical / packoff sticking signature:
            # - Reactive shale sloughing or keyseat grabs drill collars
            # - Surface torque spikes violently towards make-up / motor stall limits
            # - ROP drops to zero or near zero as drillstring cannot progress
            # - Rotary RPM stalls, standpipe pressure ramps up due to restricted annular flow
            self.torque = 32500.0 if reg == "mizoram" else 29500.0
            self.rop = 0.3
            self.rpm = 20.0
            self.wob = base['wob'] * 1.3
            self.spp_psi = base['spp_psi'] + 550.0
            self.flow_out_pct = 97.0
            self.pit_gain_bbl = 0.0
            
        else:
            # "normal" drilling baseline
            self.active_scenario = "normal"
            self.flow_out_pct = 100.0
            self.pit_gain_bbl = 0.0
            self.spp_psi = base['spp_psi']
            self.rop = base['rop']
            self.wob = base['wob']
            self.rpm = base['rpm']
            self.torque = base['torque']
            self.mud_weight = base['mud_weight']
            self.ecd = base['ecd']

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
            except Exception:
                pass
            await asyncio.sleep(1.0 / max(0.1, self.speed_multiplier))

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def seek(self, depth_tvd: float):
        self.depth_tvd = depth_tvd
        params = self._get_current_params()
        prediction = self.ml_service.predict_risk(params, self.history)
        payload = {
            "status": "success",
            "data": params,
            "prediction": prediction,
            "scenario": self.active_scenario,
            "is_running": self.is_running
        }
        await ws_manager.broadcast(payload)

    def reset(self, well_id: str = "OIL-BAGHJAN-1", depth_tvd: float = None):
        self.well_id = well_id
        base = get_well_calibrated_baseline(well_id)
        self.depth_tvd = depth_tvd if depth_tvd is not None else base.get('depth_tvd', 2240.0)
        self.set_scenario("normal")

telemetry_simulator = TelemetrySimulator()
