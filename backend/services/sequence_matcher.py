"""
Temporal Sequence Pattern Matching Service

Evaluates rolling telemetry windows against historical reference incident lead-ups
using Dynamic Time Warping (fastdtw) to detect precursor signatures before hazard onset.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from scipy.spatial.distance import euclidean  # type: ignore
from fastdtw import fastdtw


# Scale normalizers for uniform multi-channel Euclidean distance
FEATURE_SCALES = {
    "rop": 30.0,           # 0-30 m/hr
    "torque": 25000.0,      # 5,000-25,000 ft-lbf
    "wob": 25.0,           # 0-25 klbs
    "flow_out_pct": 100.0   # 50-150 %
}

WINDOW_SIZE = 10


def vectorize_point(point: Dict[str, Any]) -> List[float]:
    """Extracts and normalizes the 4 key temporal features into a normalized vector."""
    rop = float(point.get("rop", 15.0) or 15.0) / FEATURE_SCALES["rop"]
    torque = float(point.get("torque", 13000.0) or 13000.0) / FEATURE_SCALES["torque"]
    wob = float(point.get("wob", point.get("wob_klbs", 14.0)) or 14.0) / FEATURE_SCALES["wob"]
    flow = float(point.get("flow_out_pct", 100.0) or 100.0) / FEATURE_SCALES["flow_out_pct"]
    return [rop, torque, wob, flow]


def build_synthetic_reference_sequences() -> List[Dict[str, Any]]:
    """
    Constructs historical 10-step lead-up trajectories based on documented Golden PDF incidents.
    """
    # 1. Stuck Pipe Lead-Up at OIL-MORAN-1 (2832m): Torque spike, ROP collapse, overpull
    stuck_sequence = []
    for i in range(10):
        t = i / 9.0  # 0.0 to 1.0
        stuck_sequence.append({
            "rop": 15.0 * (1.0 - 0.75 * t),          # 15.0 -> 3.75 m/hr
            "torque": 13000.0 + (11000.0 * (t ** 1.5)), # 13,000 -> 24,000 lbf-ft
            "wob": 14.0 + 3.0 * np.sin(i),
            "flow_out_pct": 100.0
        })

    # 2. Lost Circulation Lead-Up at OIL-MORAN-1 (1540m): Flow-out collapse, pit volume drop
    loss_sequence = []
    for i in range(10):
        t = i / 9.0
        loss_sequence.append({
            "rop": 16.0 + 2.0 * t,
            "torque": 13200.0 + 300.0 * np.sin(i),
            "wob": 13.0,
            "flow_out_pct": 100.0 - (38.0 * t)       # 100% -> 62%
        })

    # 3. Gas Kick Lead-Up at OIL-NAHARKATIYA-1 (3105m): Drilling break ROP surge + flow increase
    kick_sequence = []
    for i in range(10):
        t = i / 9.0
        kick_sequence.append({
            "rop": 12.0 + (11.0 * (t ** 1.3)),       # 12.0 -> 23.0 m/hr (drilling break)
            "torque": 12000.0 + 1500.0 * t,
            "wob": 14.0,
            "flow_out_pct": 100.0 + (18.0 * t)       # 100% -> 118% (influx surge)
        })

    return [
        {
            "id": "stuck_pipe_moran",
            "event_type": "Stuck Pipe (Differential Sticking)",
            "hazard_key": "stuck_pipe",
            "well_id": "OIL-MORAN-1",
            "depth_tvd": 2832.0,
            "sequence": np.array([vectorize_point(p) for p in stuck_sequence])
        },
        {
            "id": "lost_circulation_moran",
            "event_type": "Severe Lost Circulation",
            "hazard_key": "lost_circulation",
            "well_id": "OIL-MORAN-1",
            "depth_tvd": 1540.0,
            "sequence": np.array([vectorize_point(p) for p in loss_sequence])
        },
        {
            "id": "gas_kick_naharkatiya",
            "event_type": "High Pressure Gas Kick",
            "hazard_key": "gas_kick",
            "well_id": "OIL-NAHARKATIYA-1",
            "depth_tvd": 3105.0,
            "sequence": np.array([vectorize_point(p) for p in kick_sequence])
        }
    ]


class SequenceMatcherService:
    _instance: Optional["SequenceMatcherService"] = None
    reference_patterns: List[Dict[str, Any]] = []
    rolling_window: List[Any] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SequenceMatcherService, cls).__new__(cls)
            cls._instance.reference_patterns = build_synthetic_reference_sequences()
            cls._instance.rolling_window = []
        return cls._instance

    def __init__(self, window_size: int = WINDOW_SIZE, alert_threshold: float = 75.0):
        self.window_size = window_size
        self.alert_threshold = alert_threshold if alert_threshold > 1.0 else alert_threshold * 100.0

    def reset(self):
        self.rolling_window = []

    def reset_buffer(self):
        """Alias for reset."""
        self.reset()

    def add_reading(self, reading: Dict[str, Any]):
        vec = vectorize_point(reading)
        self.rolling_window.append(vec)
        if len(self.rolling_window) > WINDOW_SIZE:
            self.rolling_window = self.rolling_window[-WINDOW_SIZE:]

    def evaluate_window(
        self,
        custom_window: Optional[List[Dict[str, Any]]] = None,
        similarity_threshold: float = 78.0
    ) -> Dict[str, Any]:
        """
        Computes DTW distance against reference incident lead-ups.
        Returns highest matching pattern and whether it crosses the alert threshold.
        """
        if custom_window is not None:
            seq = np.array([vectorize_point(p) for p in custom_window])
        else:
            if len(self.rolling_window) < 5:
                return {"matched": False, "best_match": None, "message": "Window accumulating readings."}
            seq = np.array(self.rolling_window)

        best_match = None
        highest_sim = 0.0
        lowest_dist = float("inf")

        for ref in self.reference_patterns:
            ref_seq = ref["sequence"]
            try:
                distance, _ = fastdtw(seq, ref_seq, dist=euclidean)
                # Linear decay bounded between 0% and 100% (max divergence cutoff 4.0)
                sim_pct = float(round(max(0.0, min(100.0, 100.0 * (1.0 - (distance / 4.0)))), 1))
            except Exception:
                distance = 99.0
                sim_pct = 0.0

            if sim_pct > highest_sim:
                highest_sim = sim_pct
                lowest_dist = float(round(distance, 3))
                best_match = {
                    "id": ref["id"],
                    "event_type": ref["event_type"],
                    "hazard_key": ref["hazard_key"],
                    "well_id": ref["well_id"],
                    "depth_tvd": ref["depth_tvd"],
                    "similarity_pct": sim_pct,
                    "distance": lowest_dist
                }

        is_matched = highest_sim >= similarity_threshold and best_match is not None
        message = ""
        if is_matched and best_match is not None:
            message = (
                f"Current drilling pattern resembles the lead-up to {best_match['event_type']} "
                f"at {best_match['well_id']} ({best_match['similarity_pct']}% pattern match)."
            )

        return {
            "matched": is_matched,
            "best_match": best_match,
            "similarity_pct": highest_sim,
            "distance": lowest_dist,
            "threshold": similarity_threshold,
            "message": message
        }

    def evaluate_telemetry_point(
        self,
        reading: Dict[str, Any],
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Convenience method to push a reading and evaluate window."""
        thresh = similarity_threshold if similarity_threshold is not None else getattr(self, "alert_threshold", 75.0)
        if thresh < 1.0:
            thresh = thresh * 100.0
        self.add_reading(reading)
        res = self.evaluate_window(similarity_threshold=thresh)
        bm = res.get("best_match")
        return {
            "matched": res.get("matched", False),
            "pattern_name": bm["event_type"] if bm else "",
            "historical_incident_id": bm["id"] if bm else "",
            "reference_well": bm["well_id"] if bm else "",
            "similarity_score": round(float(res.get("similarity_pct", 0.0) / 100.0), 4) if res.get("similarity_pct") else 0.0,
            "similarity_pct": res.get("similarity_pct", 0.0),
            "distance": res.get("distance", 0.0),
            "message": res.get("message", "")
        }



def match_telemetry_sequence(history_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One-shot utility evaluating a sequence of readings."""
    service = SequenceMatcherService()
    return service.evaluate_window(custom_window=history_records)
