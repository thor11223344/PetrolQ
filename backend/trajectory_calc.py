import hashlib
import numpy as np

def compute_realistic_trajectory(well_id: str, tvd_max: float, is_active: bool = False, db_events: list = None):
    """
    Computes a realistic 3D directional borehole trajectory.
    Uses deterministic pseudo-random seed from well_id so each well has a unique,
    consistent azimuth, build-up rate, and KOP, but fans out realistically.
    """
    seed = int(hashlib.md5(well_id.encode('utf-8')).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)
    
    # Surface wellhead position (Z=0)
    if is_active:
        x0, y0 = 0.0, 0.0
        kop = float(rng.uniform(420.0, 620.0))
        max_drift = float(rng.uniform(300.0, 500.0))
        azimuth_deg = float(rng.uniform(35.0, 75.0)) # Active rig drifts NE
    else:
        # Offsets are placed in realistic pad/cluster positions around active rig (160m - 520m)
        surface_dist = float(rng.uniform(160.0, 520.0))
        surface_az = float(rng.uniform(0.0, 2.0 * np.pi))
        x0 = surface_dist * np.sin(surface_az)
        y0 = surface_dist * np.cos(surface_az)
        kop = float(rng.uniform(320.0, 780.0))
        max_drift = float(rng.uniform(200.0, 620.0))
        azimuth_deg = float(rng.uniform(0.0, 360.0)) # Offsets fan out across all 360 degrees
        
    azimuth_rad = np.radians(azimuth_deg)
    drift_power = float(rng.uniform(1.15, 1.55))
    turn_rate = float(rng.uniform(-12.0, 12.0))
    
    num_points = 100
    depths_z = np.linspace(0, tvd_max, num_points)
    xs = np.full_like(depths_z, x0)
    ys = np.full_like(depths_z, y0)
    
    for i, z in enumerate(depths_z):
        if z > kop:
            prog = (z - kop) / max(1.0, (tvd_max - kop))
            # S-curve build and hold profile with individual curvature power
            drift = max_drift * (np.sin(prog * np.pi / 2.0) ** drift_power)
            # Subtle realistic azimuth walk / dogleg
            az_cur = azimuth_rad + np.radians(turn_rate * np.sin(prog * np.pi))
            xs[i] = x0 + drift * np.sin(az_cur)
            ys[i] = y0 + drift * np.cos(az_cur)
            
    # Differential steps along trajectory
    dx = np.diff(xs, prepend=xs[0])
    dy = np.diff(ys, prepend=ys[0])
    dz = np.diff(depths_z, prepend=depths_z[0])
    step_md = np.sqrt(dx**2 + dy**2 + dz**2)
    md = np.cumsum(step_md)
    
    # Inclination: angle from vertical (degrees)
    inc = np.degrees(np.arctan2(np.sqrt(dx**2 + dy**2), dz + 1e-6))
    
    # Azimuth: direction from North (degrees)
    az = (np.degrees(np.arctan2(dx, dy + 1e-6)) + 360.0) % 360.0
    
    # Depth-indexed risk score (0.0 to 1.0) along trajectory
    risk_scores = []
    for z in depths_z:
        if z < 1400: # Shallow Tipam: Low risk
            r = 0.12 + 0.08 * np.sin(z / 200.0)
        elif z < 2100: # Upper Barail transition: Moderate risk
            r = 0.35 + 0.15 * np.sin(z / 150.0)
        elif z < 2750: # Known Barail kick & loss overpressure zone: High/Critical risk
            peak_factor = np.exp(-((z - 2480.0) / 200.0) ** 2)
            r = 0.55 + 0.38 * peak_factor
        else: # Deep Kopili: Elevated pressure
            r = 0.42 + 0.12 * np.sin(z / 180.0)
        risk_scores.append(round(float(np.clip(r, 0.05, 0.98)), 3))
        
    # Formation tops for this well (Assam shelf basin)
    formation_specs = [
        ("Tipam Sandstone", min(tvd_max * 0.42, 1450.0), "#EAB308", "Freshwater permeable sand reservoir"),
        ("Barail Formation", min(tvd_max * 0.68, 2400.0), "#F97316", "Overpressured sand-shale (Known Kick Zone)"),
        ("Kopili Formation", min(tvd_max * 0.85, 2950.0), "#A855F7", "Deep marine shale transition")
    ]
    
    # Check if we have specific events with formation depths
    if db_events:
        for ev in db_events:
            if ev.formation and ev.depth_start_tvd and ev.depth_start_tvd < tvd_max:
                fname = f"{ev.formation} Top"
                fcolor = "#EF4444" if "kick" in (ev.event_type or "").lower() else "#38BDF8"
                fdesc = f"Historical {ev.event_type} at {round(ev.depth_start_tvd, 1)}m"
                formation_specs.append((fname, ev.depth_start_tvd, fcolor, fdesc))
                
    formation_tops = []
    seen_depths = set()
    for name, target_tvd, color, desc in formation_specs:
        if target_tvd < tvd_max:
            idx = int(np.argmin(np.abs(depths_z - target_tvd)))
            tvd_val = round(float(depths_z[idx]), 1)
            if tvd_val in seen_depths:
                continue
            seen_depths.add(tvd_val)
            formation_tops.append({
                "name": name,
                "tvd": tvd_val,
                "md": round(float(md[idx]), 1),
                "x": round(float(xs[idx]), 1),
                "y": round(float(ys[idx]), 1),
                "z": tvd_val,
                "color": color,
                "description": desc
            })
            
    return {
        "well_id": well_id,
        "is_active": is_active,
        "surface": {"x": round(float(x0), 1), "y": round(float(y0), 1), "z": 0.0},
        "tvd_max": round(float(tvd_max), 1),
        "total_md": round(float(md[-1]), 1),
        "kop": round(float(kop), 1),
        "trajectory": {
            "x": [round(float(val), 2) for val in xs],
            "y": [round(float(val), 2) for val in ys],
            "z": [round(float(val), 2) for val in depths_z],
            "md": [round(float(val), 2) for val in md],
            "inclination": [round(float(val), 1) for val in inc],
            "azimuth": [round(float(val), 1) for val in az],
            "risk_scores": risk_scores
        },
        "formation_tops": formation_tops
    }

def compute_anti_collision(active_traj: dict, offset_traj: dict):
    pts_a = np.column_stack([active_traj["trajectory"]["x"], active_traj["trajectory"]["y"], active_traj["trajectory"]["z"]])
    pts_b = np.column_stack([offset_traj["trajectory"]["x"], offset_traj["trajectory"]["y"], offset_traj["trajectory"]["z"]])
    
    # Evaluate subsurface points (below surface casing, Z >= 30m) to isolate directional borehole convergence
    sub_mask_a = np.array(active_traj["trajectory"]["z"]) >= 30.0
    sub_mask_b = np.array(offset_traj["trajectory"]["z"]) >= 30.0
    
    if np.any(sub_mask_a) and np.any(sub_mask_b):
        pts_a_eval = pts_a[sub_mask_a]
        pts_b_eval = pts_b[sub_mask_b]
        indices_a = np.where(sub_mask_a)[0]
        indices_b = np.where(sub_mask_b)[0]
    else:
        pts_a_eval = pts_a
        pts_b_eval = pts_b
        indices_a = np.arange(len(pts_a))
        indices_b = np.arange(len(pts_b))

    # Pairwise 3D Euclidean distances
    diff = pts_a_eval[:, np.newaxis, :] - pts_b_eval[np.newaxis, :, :]
    dist_matrix = np.sqrt(np.sum(diff**2, axis=-1))
    
    min_idx_flat = np.argmin(dist_matrix)
    idx_a_eval, idx_b_eval = np.unravel_index(min_idx_flat, dist_matrix.shape)
    
    orig_idx_a = indices_a[idx_a_eval]
    orig_idx_b = indices_b[idx_b_eval]
    min_dist = float(dist_matrix[idx_a_eval, idx_b_eval])
    
    # Standard directional drilling error-ellipse separation factor
    # SF = D / (uncertainty_a + uncertainty_b)
    # ISCWSA error model simplified: sigma ~ 1.5m per 1000m MD
    md_a = active_traj["trajectory"]["md"][orig_idx_a]
    md_b = offset_traj["trajectory"]["md"][orig_idx_b]
    sigma_combined = max(5.0, (md_a + md_b) * 0.0018)
    separation_factor = round(min_dist / sigma_combined, 2)
    
    # Industry status: SF < 1.5 -> CRITICAL; 1.5 <= SF < 3.0 -> CAUTION; >= 3.0 -> SAFE
    if separation_factor < 1.5:
        status = "CRITICAL"
        color = "#EF4444"
    elif separation_factor < 3.0:
        status = "CAUTION"
        color = "#F59E0B"
    else:
        status = "SAFE"
        color = "#10B981"
        
    return {
        "offset_well_id": offset_traj["well_id"],
        "min_distance_m": round(min_dist, 1),
        "separation_factor": separation_factor,
        "status": status,
        "color": color,
        "closest_point_active": {
            "x": active_traj["trajectory"]["x"][orig_idx_a],
            "y": active_traj["trajectory"]["y"][orig_idx_a],
            "z": active_traj["trajectory"]["z"][orig_idx_a],
            "md": md_a,
            "tvd": active_traj["trajectory"]["z"][orig_idx_a]
        },
        "closest_point_offset": {
            "x": offset_traj["trajectory"]["x"][orig_idx_b],
            "y": offset_traj["trajectory"]["y"][orig_idx_b],
            "z": offset_traj["trajectory"]["z"][orig_idx_b],
            "md": md_b,
            "tvd": offset_traj["trajectory"]["z"][orig_idx_b]
        },
        "active_point": {
            "x": active_traj["trajectory"]["x"][orig_idx_a],
            "y": active_traj["trajectory"]["y"][orig_idx_a],
            "z": active_traj["trajectory"]["z"][orig_idx_a],
            "md": md_a,
            "tvd": active_traj["trajectory"]["z"][orig_idx_a]
        },
        "offset_point": {
            "x": offset_traj["trajectory"]["x"][orig_idx_b],
            "y": offset_traj["trajectory"]["y"][orig_idx_b],
            "z": offset_traj["trajectory"]["z"][orig_idx_b],
            "md": md_b,
            "tvd": offset_traj["trajectory"]["z"][orig_idx_b]
        }
    }
