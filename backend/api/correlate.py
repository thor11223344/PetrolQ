from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import WellLog
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import numpy as np

router = APIRouter()

@router.get("/api/correlate")
def correlate_wells(
    active_well: str = Query(..., description="Active Well ID"),
    offset_well: str = Query(..., description="Offset Well ID"),
    db: Session = Depends(get_db)
):
    # Fetch logs for active well
    active_logs = db.query(WellLog).filter(
        WellLog.well_id == active_well,
        WellLog.gamma_ray.isnot(None),
        WellLog.depth_tvd.isnot(None)
    ).order_by(WellLog.depth_tvd).all()

    if not active_logs:
        raise HTTPException(status_code=404, detail=f"No valid GR logs found for active well {active_well}")

    # Fetch logs for offset well
    offset_logs = db.query(WellLog).filter(
        WellLog.well_id == offset_well,
        WellLog.gamma_ray.isnot(None),
        WellLog.depth_tvd.isnot(None)
    ).order_by(WellLog.depth_tvd).all()

    if not offset_logs:
        raise HTTPException(status_code=404, detail=f"No valid GR logs found for offset well {offset_well}")

    # Extract depth and GR arrays
    active_depths = [log.depth_tvd for log in active_logs]
    active_gr = [log.gamma_ray for log in active_logs]
    
    offset_depths = [log.depth_tvd for log in offset_logs]
    offset_gr = [log.gamma_ray for log in offset_logs]

    # Convert to numpy arrays for fastdtw
    a_gr_np = np.array(active_gr).reshape(-1, 1)
    o_gr_np = np.array(offset_gr).reshape(-1, 1)

    # Calculate DTW
    distance, path = fastdtw(a_gr_np, o_gr_np, dist=euclidean)

    # Path is a list of tuples (active_idx, offset_idx)
    # Convert tuples to lists for JSON serialization
    mapping = [[int(i), int(j)] for i, j in path]

    return {
        "active_well": active_well,
        "offset_well": offset_well,
        "active_depths": active_depths,
        "active_gr": active_gr,
        "offset_depths": offset_depths,
        "offset_gr": offset_gr,
        "mapping": mapping,
        "distance": float(distance)
    }

@router.get("/api/wells/casing-cement-correlation")
@router.get("/api/casing-cement-correlation")
def get_casing_cement_correlation(
    active_well: str = Query("OIL-BAGHJAN-1", description="Active Well ID"),
    db: Session = Depends(get_db)
):
    """
    Casing & Cementing Correlation across Active Well and Proximate Offset Wells.
    Compares casing strings, set depths, burst/collapse ratings, shoe formations, 
    slurry designs, TOC, LOT/FIT test values, and historical cementing integrity challenges.
    """
    wells_data = [
        {
            "well_id": active_well,
            "role": "Active Planned Well",
            "field": "Baghjan",
            "total_depth_tvd": 3600.0,
            "casing_strings": [
                {
                    "name": 'Conductor (20")',
                    "hole_size_in": 26.0,
                    "casing_od_in": 20.0,
                    "depth_tvd_m": 70.0,
                    "weight_ppf": 94.0,
                    "grade": "K-55",
                    "shoe_formation": "Alluvium / Dihing",
                    "toc_tvd_m": 0.0,
                    "slurry_type": "Class G Neat",
                    "slurry_density_ppg": 15.6,
                    "lot_emw_ppg": 11.5,
                    "integrity_notes": "Surface isolation verified by top-out cement returns."
                },
                {
                    "name": 'Surface Casing (13-3/8")',
                    "hole_size_in": 17.5,
                    "casing_od_in": 13.375,
                    "depth_tvd_m": 680.0,
                    "weight_ppf": 68.0,
                    "grade": "L-80",
                    "shoe_formation": "Upper Tipam Sandstone",
                    "toc_tvd_m": 0.0,
                    "slurry_type": "Class G + 4% Bentonite Lead (13.5 ppg) / Neat Tail (15.8 ppg)",
                    "slurry_density_ppg": 15.8,
                    "lot_emw_ppg": 13.8,
                    "integrity_notes": "Protects fresh water aquifer sands. Centralizers placed 1 per 2 joints across aquifers."
                },
                {
                    "name": 'Intermediate Casing (9-5/8")',
                    "hole_size_in": 12.25,
                    "casing_od_in": 9.625,
                    "depth_tvd_m": 2280.0,
                    "weight_ppf": 47.0,
                    "grade": "P-110",
                    "shoe_formation": "Top Barail Kick Transition",
                    "toc_tvd_m": 450.0,
                    "slurry_type": "Latex-modified gas-tight anti-channeling slurry",
                    "slurry_density_ppg": 16.0,
                    "lot_emw_ppg": 16.5,
                    "integrity_notes": "Vital barrier seated 40m above abnormal Barail gas ramp. Shoe test required to 16.5 ppg EMW."
                },
                {
                    "name": 'Production Liner (7")',
                    "hole_size_in": 8.5,
                    "casing_od_in": 7.0,
                    "depth_tvd_m": 3520.0,
                    "weight_ppf": 29.0,
                    "grade": "Q-125",
                    "shoe_formation": "Kopili Marine Shale",
                    "toc_tvd_m": 2180.0,
                    "slurry_type": "High-temperature gas-migration polymer slurry (fluid loss < 25 mL)",
                    "slurry_density_ppg": 16.4,
                    "lot_emw_ppg": 17.8,
                    "integrity_notes": "Overlaps 9-5/8 casing by 100m. Requires premium gas-tight flush joint connections."
                }
            ]
        },
        {
            "well_id": "OIL-BAGHJAN-4",
            "role": "Offset Well (1.8 km NE)",
            "field": "Baghjan",
            "total_depth_tvd": 3550.0,
            "casing_strings": [
                {
                    "name": 'Conductor (20")',
                    "hole_size_in": 26.0,
                    "casing_od_in": 20.0,
                    "depth_tvd_m": 65.0,
                    "weight_ppf": 94.0,
                    "grade": "K-55",
                    "shoe_formation": "Alluvium",
                    "toc_tvd_m": 0.0,
                    "slurry_type": "Class G Neat",
                    "slurry_density_ppg": 15.6,
                    "lot_emw_ppg": 11.4,
                    "integrity_notes": "Good surface returns observed."
                },
                {
                    "name": 'Surface Casing (13-3/8")',
                    "hole_size_in": 17.5,
                    "casing_od_in": 13.375,
                    "depth_tvd_m": 650.0,
                    "weight_ppf": 68.0,
                    "grade": "K-55",
                    "shoe_formation": "Upper Tipam",
                    "toc_tvd_m": 0.0,
                    "slurry_type": "Class G Lead & Tail",
                    "slurry_density_ppg": 15.6,
                    "lot_emw_ppg": 13.5,
                    "integrity_notes": "Experienced minor seepage during displacement (15 bbl)."
                },
                {
                    "name": 'Intermediate Casing (9-5/8")',
                    "hole_size_in": 12.25,
                    "casing_od_in": 9.625,
                    "depth_tvd_m": 2240.0,
                    "weight_ppf": 47.0,
                    "grade": "N-80",
                    "shoe_formation": "Barail Transition",
                    "toc_tvd_m": 620.0,
                    "slurry_type": "Standard Class G + retarder",
                    "slurry_density_ppg": 15.8,
                    "lot_emw_ppg": 16.1,
                    "integrity_notes": "WARNING: Sustained casing pressure (SCP) 320 psi recorded after 18 months due to micro-annulus gas channeling. Squeeze job performed."
                },
                {
                    "name": 'Production Liner (7")',
                    "hole_size_in": 8.5,
                    "casing_od_in": 7.0,
                    "depth_tvd_m": 3480.0,
                    "weight_ppf": 29.0,
                    "grade": "P-110",
                    "shoe_formation": "Kopili",
                    "toc_tvd_m": 2150.0,
                    "slurry_type": "Latex gas-tight slurry",
                    "slurry_density_ppg": 16.2,
                    "lot_emw_ppg": 17.4,
                    "integrity_notes": "Liner top packer set and pressure tested successfully to 3500 psi."
                }
            ]
        },
        {
            "well_id": "OIL-NAHARKATIYA-1",
            "role": "Regional Benchmark (31.2 km SW)",
            "field": "Naharkatiya",
            "total_depth_tvd": 3450.0,
            "casing_strings": [
                {
                    "name": 'Conductor (20")',
                    "hole_size_in": 26.0,
                    "casing_od_in": 20.0,
                    "depth_tvd_m": 60.0,
                    "weight_ppf": 94.0,
                    "grade": "K-55",
                    "shoe_formation": "Alluvium",
                    "toc_tvd_m": 0.0,
                    "slurry_type": "Class G Neat",
                    "slurry_density_ppg": 15.6,
                    "lot_emw_ppg": 11.2,
                    "integrity_notes": "Good returns."
                },
                {
                    "name": 'Surface Casing (13-3/8")',
                    "hole_size_in": 17.5,
                    "casing_od_in": 13.375,
                    "depth_tvd_m": 620.0,
                    "weight_ppf": 68.0,
                    "grade": "J-55",
                    "shoe_formation": "Tipam Sand",
                    "toc_tvd_m": 50.0,
                    "slurry_type": "Lightweight Pozzolanic slurry",
                    "slurry_density_ppg": 14.8,
                    "lot_emw_ppg": 13.2,
                    "integrity_notes": "Lost 42 bbl slurry into depleted shallow sands during cement job."
                },
                {
                    "name": 'Intermediate Casing (9-5/8")',
                    "hole_size_in": 12.25,
                    "casing_od_in": 9.625,
                    "depth_tvd_m": 2100.0,
                    "weight_ppf": 40.0,
                    "grade": "N-80",
                    "shoe_formation": "Barail Coal transition",
                    "toc_tvd_m": 580.0,
                    "slurry_type": "Class G + Silica Flour",
                    "slurry_density_ppg": 15.9,
                    "lot_emw_ppg": 15.8,
                    "integrity_notes": "Shoe tested to 15.8 ppg; required barite pill during drill-out."
                },
                {
                    "name": 'Production Liner (7")',
                    "hole_size_in": 8.5,
                    "casing_od_in": 7.0,
                    "depth_tvd_m": 3390.0,
                    "weight_ppf": 26.0,
                    "grade": "N-80",
                    "shoe_formation": "Kopili Shale",
                    "toc_tvd_m": 2020.0,
                    "slurry_type": "Class G + Micro-matrix",
                    "slurry_density_ppg": 16.0,
                    "lot_emw_ppg": 17.0,
                    "integrity_notes": "Good cement bond log (CBL/VDL) amplitude across reservoir interval."
                }
            ]
        }
    ]

    return {
        "active_well": active_well,
        "offsets_analyzed": len(wells_data) - 1,
        "comparison": wells_data,
        "recommended_practices": [
            "Use P-110 grade casing for 9-5/8 intermediate string to withstand Barail gas kick shut-in pressures > 4500 psi.",
            "Incorporate gas-block latex additives in 9-5/8 and 7 liner cement slurries to prevent gas percolation observed in OIL-BAGHJAN-4.",
            "Run solid centralizers across permeable Tipam sandstones to optimize mud removal displacement efficiency (> 85%).",
            "Perform Leak-Off Test (LOT) immediately below 9-5/8 shoe to verify at least 16.5 ppg equivalent mud weight before entering Barail pay."
        ]
    }

@router.get("/api/wells/stratigraphic-cross-section")
@router.get("/api/stratigraphic-cross-section")
def get_stratigraphic_cross_section(
    active_well: str = Query("OIL-BAGHJAN-1", description="Active Well ID"),
    db: Session = Depends(get_db)
):
    """
    CORRECTION 5 REQUIREMENT:
    3-well side-by-side Stratigraphic Cross-Section (fence diagram)
    reusing the exact formation color scheme from the Realistic Geology 3D theme:
      - Alluvium / Dihing: #64748B
      - Tipam Sandstone: #EAB308
      - Barail Formation: #F97316
      - Kopili Formation: #A855F7
      - Jaintia / Basement: #06B6D4
    """
    # 3 wells side by side: West offset -> Active Well -> East offset
    wells = [
        {
            "well_id": "OIL-NAHARKATIYA-1",
            "name": "Naharkatiya-1 (West Offset)",
            "x_offset_km": 0.0,
            "kb_elevation_m": 108.0,
            "total_depth_tvd_m": 3450.0,
            "is_active": False,
            "formations": [
                {"name": "Alluvium / Dihing", "top_tvd": 0.0, "base_tvd": 1050.0, "color": "#64748B", "lithology": "Unconsolidated Gravels & Sands"},
                {"name": "Tipam Sandstone", "top_tvd": 1050.0, "base_tvd": 2040.0, "color": "#EAB308", "lithology": "Coarse Permeable Sandstone / Aquifers"},
                {"name": "Barail Formation", "top_tvd": 2040.0, "base_tvd": 2820.0, "color": "#F97316", "lithology": "Overpressured Gas Sand & Coal"},
                {"name": "Kopili Formation", "top_tvd": 2820.0, "base_tvd": 3250.0, "color": "#A855F7", "lithology": "Deep Marine Fissile Shale"},
                {"name": "Jaintia / Basement", "top_tvd": 3250.0, "base_tvd": 3450.0, "color": "#06B6D4", "lithology": "Dense Fossiliferous Limestone"}
            ],
            "incidents": [
                {"depth_tvd": 1450.0, "type": "Seepage Loss (35 bbl)", "severity": "MEDIUM", "formation": "Tipam Sandstone"},
                {"depth_tvd": 2180.0, "type": "Gas Influx (12 bbl)", "severity": "HIGH", "formation": "Barail Formation"}
            ]
        },
        {
            "well_id": active_well,
            "name": f"{active_well} (Active Planned Well)",
            "x_offset_km": 15.5,
            "kb_elevation_m": 115.0,
            "total_depth_tvd_m": 3600.0,
            "is_active": True,
            "formations": [
                {"name": "Alluvium / Dihing", "top_tvd": 0.0, "base_tvd": 1200.0, "color": "#64748B", "lithology": "Surface Gravels & Clay Beds"},
                {"name": "Tipam Sandstone", "top_tvd": 1200.0, "base_tvd": 2400.0, "color": "#EAB308", "lithology": "Massive Bedded Sandstone"},
                {"name": "Barail Formation", "top_tvd": 2400.0, "base_tvd": 2950.0, "color": "#F97316", "lithology": "Overpressured Gas/Condensate Sands"},
                {"name": "Kopili Formation", "top_tvd": 2950.0, "base_tvd": 3400.0, "color": "#A855F7", "lithology": "Reactive Marine Shales"},
                {"name": "Jaintia / Basement", "top_tvd": 3400.0, "base_tvd": 3600.0, "color": "#06B6D4", "lithology": "Basin Limestone & Crystalline Basement"}
            ],
            "incidents": []
        },
        {
            "well_id": "OIL-BAGHJAN-4",
            "name": "Baghjan-4 (East Offset)",
            "x_offset_km": 17.3,
            "kb_elevation_m": 118.0,
            "total_depth_tvd_m": 3550.0,
            "is_active": False,
            "formations": [
                {"name": "Alluvium / Dihing", "top_tvd": 0.0, "base_tvd": 1215.0, "color": "#64748B", "lithology": "Superficial Gravels"},
                {"name": "Tipam Sandstone", "top_tvd": 1215.0, "base_tvd": 2420.0, "color": "#EAB308", "lithology": "Coarse Sandstone"},
                {"name": "Barail Formation", "top_tvd": 2420.0, "base_tvd": 2965.0, "color": "#F97316", "lithology": "High Pressure Gas Sandstone & Coal"},
                {"name": "Kopili Formation", "top_tvd": 2965.0, "base_tvd": 3420.0, "color": "#A855F7", "lithology": "Marine Fissile Mudstones"},
                {"name": "Jaintia / Basement", "top_tvd": 3420.0, "base_tvd": 3550.0, "color": "#06B6D4", "lithology": "Sylhet Limestone Member"}
            ],
            "incidents": [
                {"depth_tvd": 2418.0, "type": "Critical Gas Kick (22 bbl, 4200 psi)", "severity": "CRITICAL", "formation": "Barail Formation"},
                {"depth_tvd": 3020.0, "type": "Packoff / Tight Hole (110 klbf overpull)", "severity": "HIGH", "formation": "Kopili Formation"}
            ]
        }
    ]

    # Correlative formation boundaries (tie-lines connecting tops across the 3 wells)
    tie_lines = [
        {
            "formation": "Tipam Sandstone",
            "color": "#EAB308",
            "tops": [1050.0, 1200.0, 1215.0],
            "structural_dip_trend": "Gentle east-northeast regional dip (~1.8 deg)"
        },
        {
            "formation": "Barail Formation",
            "color": "#F97316",
            "tops": [2040.0, 2400.0, 2420.0],
            "structural_dip_trend": "Significant downward dip from Naharkatiya to Baghjan graben (+360m TVD)"
        },
        {
            "formation": "Kopili Formation",
            "color": "#A855F7",
            "tops": [2820.0, 2950.0, 2965.0],
            "structural_dip_trend": "Deep marine regional datum with consistent stratigraphic continuity"
        },
        {
            "formation": "Jaintia / Basement",
            "color": "#06B6D4",
            "tops": [3250.0, 3400.0, 3420.0],
            "structural_dip_trend": "Basin floor slope with potential horst-graben boundary faults"
        }
    ]

    return {
        "active_well": active_well,
        "wells_count": len(wells),
        "cross_section_orientation": "SW to NE (Naharkatiya -> Baghjan)",
        "wells": wells,
        "tie_lines": tie_lines,
        "geological_summary": (
            "Regional structural cross-section across the Upper Assam Shelf. "
            "Formations deepen systematically from Naharkatiya in the southwest towards the Baghjan depression in the northeast. "
            "The Barail overpressure gas sequence is encountered ~360m deeper in Baghjan than Naharkatiya, "
            "with severe gas kick and well control history confirmed at 2,418m TVD in adjacent offset OIL-BAGHJAN-4."
        )
    }
