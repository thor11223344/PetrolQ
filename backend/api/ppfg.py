from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import numpy as np

from database import get_db
from models import WellMaster, DrillingParam

router = APIRouter()

@router.get("/api/wells/{well_id}/ppfg")
def get_ppfg_safe_window(
    well_id: str,
    db: Session = Depends(get_db)
):
    """
    Pore Pressure & Fracture Gradient (PPFG) Safe Mud Weight Window:
    Pore pressure and fracture gradient computed using Eaton's method (1972) with a synthetic
    sonic-log input calibrated to produce a plausible Upper Assam Basin overpressure signature
    — real acoustic log data was not available.
    Generates depth-indexed Pore Pressure and Fracture Gradient curves (in ppg and sg)
    alongside casing shoe depths and the active rig's current Equivalent Circulating Density (ECD).
    """
    well = db.query(WellMaster).filter(WellMaster.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found")

    tvd_max = well.total_depth_tvd or 3500.0
    num_pts = 80
    depths_tvd = np.linspace(50.0, tvd_max, num_pts)

    # -------------------------------------------------------------------------
    # GENUINE EATON'S METHOD (1972) PORE PRESSURE & FRACTURE GRADIENT
    # -------------------------------------------------------------------------
    # SIMPLIFIED: constant overburden gradient, not integrated from density log
    sigma_v = 19.2  # ppg (~1.0 psi/ft) Overburden stress gradient
    p_hyd = 8.6     # ppg (~0.447 psi/ft) Normal hydrostatic gradient
    eaton_n = 3.0   # Standard published Eaton acoustic transit time exponent for shales

    # 1. Normal Compaction Trend (sonic-based):
    # Δtn(z) = 185 * exp(-0.0003 * z) [μs/ft, normal shale compaction trend]
    dt_n = 185.0 * np.exp(-0.0003 * depths_tvd)

    # 2. Observed Acoustic Transit Time Δtobs(z):
    # SYNTHETIC: Δtobs derived to produce a plausible Upper Assam overpressure signature in absence of real sonic log data; Eaton formula and exponent (N=3.0) are the genuine published method.
    dt_obs = []
    for i, z in enumerate(depths_tvd):
        if z < 1200.0:
            # Hydrostatic regime (Tipam & shallow sands)
            factor = 1.0
        elif z < 2100.0:
            # Gentle transition towards top of Barail
            factor = 1.0 + 0.02 * ((z - 1200.0) / 900.0)
        elif z < 2800.0:
            # Undercompacted overpressure zone in Barail Formation
            ramp = (z - 2100.0) / 700.0
            factor = 1.02 + 0.145 * (ramp ** 1.3)
        else:
            # Elevated pore pressure regime into Kopili
            factor = 1.165 + 0.01 * np.sin((z - 2800.0) / 200.0)
        dt_obs.append(float(dt_n[i] * factor))

    dt_obs = np.array(dt_obs)

    # 3. Eaton Pore Pressure Equation:
    # Pp(z) = σv(z) - [σv(z) - Phyd(z)] * (Δtn(z) / Δtobs(z))^N
    dt_ratio = dt_n / dt_obs
    pp_raw = sigma_v - (sigma_v - p_hyd) * (dt_ratio ** eaton_n)
    pp_curve = [round(float(p), 2) for p in pp_raw]

    # Compute uncertainty bounds (±5% to ±8%) around Eaton pore pressure curve
    # Reflects confidence range given synthetic sonic-log input:
    # Narrower (±5.0%) in normal hydrostatic compaction regime (<1200m)
    # Wider (up to ±8.0%) where synthetic Δtobs deviates from normal trend (2200-2800m overpressure zone)
    pp_lower = []
    pp_upper = []
    for i, z in enumerate(depths_tvd):
        dev = max(0.0, float((dt_obs[i] - dt_n[i]) / dt_n[i]))
        unc_pct = 0.05 + min(0.03, dev * 0.18)  # 5.0% to 8.0%
        p_val = pp_raw[i]
        pp_lower.append(round(float(p_val * (1.0 - unc_pct)), 2))
        pp_upper.append(round(float(p_val * (1.0 + unc_pct)), 2))

    # 4. Eaton Fracture Gradient Equation:
    # FG(z) = Pp(z) + [ν(z) / (1 - ν(z))] * [σv(z) - Pp(z)]
    # ν(z) = 0.25 + 0.15 * (z / 3500)
    nu_z = 0.25 + 0.15 * (depths_tvd / 3500.0)
    stress_ratio = nu_z / (1.0 - nu_z)
    fg_raw = pp_raw + stress_ratio * (sigma_v - pp_raw)
    fg_curve = [round(float(f), 2) for f in fg_raw]

    # 3. Casing Shoe Seating Depths
    # SYNTHETIC: casing depths estimated, not from real schema data
    casing_shoes = [
        {"casing_type": 'Conductor 20"', "tvd_depth": 65.0, "color": "#94A3B8", "notes": "Structural integrity & shallow gravel isolation"},
        {"casing_type": 'Surface Casing 13-3/8"', "tvd_depth": 650.0, "color": "#38BDF8", "notes": "Isolates Upper Dihing & shallow freshwater sands"},
        {"casing_type": 'Intermediate Casing 9-5/8"', "tvd_depth": 2250.0, "color": "#F59E0B", "notes": "Set above high-pressure Barail kick zone"},
        {"casing_type": 'Production Liner 7"', "tvd_depth": min(3200.0, tvd_max - 150.0), "color": "#10B981", "notes": "Covers Barail pay zone into Kopili basement"}
    ]

    # 4. Retrieve Active Rig Current Telemetry
    latest_param = db.query(DrillingParam).filter(
        DrillingParam.well_id == well_id
    ).order_by(DrillingParam.timestamp.desc()).first()

    current_tvd = latest_param.depth_tvd if latest_param else 2240.0
    current_mw = latest_param.mud_weight if latest_param else 11.2
    current_ecd = latest_param.ecd if latest_param else 11.6

    # Interpolate pore pressure and fracture gradient at current depth
    current_pp = float(np.interp(current_tvd, depths_tvd, pp_curve))
    current_fg = float(np.interp(current_tvd, depths_tvd, fg_curve))

    # Evaluate safety envelope
    margin_to_kick = round(current_ecd - current_pp, 2)
    margin_to_loss = round(current_fg - current_ecd, 2)

    if current_ecd < current_pp:
        operating_status = "CRITICAL_UNDERBALANCED"
        status_message = f"DANGER: ECD ({current_ecd} ppg) is below Pore Pressure ({round(current_pp, 2)} ppg). High risk of influx/gas kick!"
        status_color = "#EF4444"
    elif current_ecd > current_fg:
        operating_status = "CRITICAL_OVER_FRACTURE"
        status_message = f"DANGER: ECD ({current_ecd} ppg) exceeds Fracture Gradient ({round(current_fg, 2)} ppg). Severe lost circulation imminent!"
        status_color = "#EF4444"
    elif margin_to_kick < 0.5:
        operating_status = "CAUTION_LOW_OVERBALANCE"
        status_message = f"CAUTION: Narrow trip margin ({margin_to_kick} ppg above pore pressure). Pre-treat active pits."
        status_color = "#F59E0B"
    elif margin_to_loss < 0.8:
        operating_status = "CAUTION_HIGH_ECD"
        status_message = f"CAUTION: Operating close to formation breakdown ({margin_to_loss} ppg margin). Monitor annular pressure losses."
        status_color = "#F59E0B"
    else:
        operating_status = "OPTIMAL_SAFE_WINDOW"
        status_message = f"SAFE: Operating safely inside the mud weight window (+{margin_to_kick} ppg overbalance, -{margin_to_loss} ppg below fracture limit)."
        status_color = "#10B981"

    # Formation reference tops
    formations = [
        {"name": "Tipam Sandstone", "top_tvd": 1200.0, "bottom_tvd": 2200.0, "color": "#EAB308"},
        {"name": "Barail Formation", "top_tvd": 2200.0, "bottom_tvd": 2950.0, "color": "#F97316"},
        {"name": "Kopili Formation", "top_tvd": 2950.0, "bottom_tvd": tvd_max, "color": "#A855F7"}
    ]

    return {
        "well_id": well_id,
        "tvd_max": tvd_max,
        "depths_tvd": [round(float(d), 1) for d in depths_tvd],
        "pore_pressure_ppg": pp_curve,
        "pore_pressure_lower_ppg": pp_lower,
        "pore_pressure_upper_ppg": pp_upper,
        "fracture_gradient_ppg": fg_curve,
        # Convert to specific gravity (sg) as well (ppg / 8.33)
        "pore_pressure_sg": [round(p / 8.33, 3) for p in pp_curve],
        "pore_pressure_lower_sg": [round(p / 8.33, 3) for p in pp_lower],
        "pore_pressure_upper_sg": [round(p / 8.33, 3) for p in pp_upper],
        "fracture_gradient_sg": [round(f / 8.33, 3) for f in fg_curve],
        "uncertainty_metadata": {
            "band_percentage": "±5.0% to ±8.0%",
            "basis": "Synthetic sonic log calibration proxy divergence",
            "description": "Uncertainty band reflects confidence range from using synthetic sonic-log proxy calibrated to regional overpressure signatures rather than real acoustic wireline logs. Band widens to ±8% in the Barail overpressure transition (2200–2800m) and narrows to ±5% in the hydrostatic interval."
        },
        "casing_shoes": casing_shoes,
        "formations": formations,
        "eaton_metadata": {
            "method": "Eaton's Method (1972)",
            "normal_compaction_trend": "Δtn(z) = 185 * exp(-0.0003 * z) μs/ft",
            "eaton_exponent_N": 3.0,
            "overburden_gradient_ppg": 19.2,
            "hydrostatic_gradient_ppg": 8.6,
            "poisson_ratio_formula": "ν(z) = 0.25 + 0.15 * (z / 3500)",
            "notes": "Pore pressure and fracture gradient computed using Eaton's method (1972) with a synthetic sonic-log input calibrated to produce a plausible Upper Assam Basin overpressure signature — real acoustic log data was not available."
        },
        "active_status": {
            "current_tvd": round(current_tvd, 1),
            "mud_weight_ppg": round(current_mw, 2),
            "ecd_ppg": round(current_ecd, 2),
            "pore_pressure_at_depth": round(current_pp, 2),
            "fracture_gradient_at_depth": round(current_fg, 2),
            "kick_margin_ppg": margin_to_kick,
            "loss_margin_ppg": margin_to_loss,
            "operating_status": operating_status,
            "status_message": status_message,
            "status_color": status_color
        }
    }
