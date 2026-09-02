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
