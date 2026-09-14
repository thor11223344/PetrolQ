from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import shutil
import uuid
import lasio
import pandas as pd

from database import get_db
from sqlalchemy.orm import Session
from models import SyntheticEvent, WellLog, WellMaster
from nlp.config import get_embedding

router = APIRouter()

class ContributeLessonSchema(BaseModel):
    well_id: str
    event_type: str = Field(..., description="e.g. Lost Circulation, Gas Kick, Stuck Pipe, Packoff")
    formation: str = Field(..., description="e.g. Barail Formation, Tipam Sandstone, Kopili")
    depth_tvd: float
    severity: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    root_cause: str
    mitigation_applied: str
    npt_hours: Optional[float] = 0.0

@router.post("/api/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    well_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Multi-format file ingestion endpoint:
    Supports PDF reports (with OCR fallback for scanned reports) and
    LAS well log files (Log ASCII Standard).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    filename = file.filename
    filename_lower = filename.lower()
    is_pdf = filename_lower.endswith('.pdf')
    is_las = filename_lower.endswith('.las')

    if not is_pdf and not is_las:
        raise HTTPException(status_code=400, detail="Only PDF reports and LAS well log files are supported.")
        
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
    
    try:
        # Save uploaded file to disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if is_pdf:
            # Ingest PDF report with OCR fallback
            from nlp.ingest import ingest_report
            result = ingest_report(temp_file_path, well_id, db)
            return {
                "status": "success",
                "file_type": "pdf",
                "filename": file.filename,
                "ocr_triggered": result.get("ocr_triggered", False),
                "extracted_count": result.get("extracted_count", 0),
                "message": f"Successfully parsed {file.filename} with {result.get('extracted_count', 0)} incidents extracted.",
                "events": result.get("events", []),
                "guardrail_verified": result.get("guardrail_verified", True),
                "guardrail_violations": result.get("guardrail_violations", [])
            }

        elif is_las:
            # Parse LAS well log file using lasio
            las = lasio.read(temp_file_path)
            df = las.df().reset_index()

            # Identify curve columns case-insensitively
            cols_lower = {col.lower(): col for col in df.columns}
            depth_col = next((cols_lower[c] for c in ['dept', 'depth', 'tvd'] if c in cols_lower), df.columns[0])
            gr_col = next((cols_lower[c] for c in ['gr', 'gamma', 'gam'] if c in cols_lower), None)
            res_col = next((cols_lower[c] for c in ['res', 'ild', 'rt', 'at90'] if c in cols_lower), None)
            sonic_col = next((cols_lower[c] for c in ['dt', 'sonic', 'ac'] if c in cols_lower), None)
            dens_col = next((cols_lower[c] for c in ['rhob', 'den', 'density'] if c in cols_lower), None)

            # Subsample to avoid massive inserts (e.g. 1 sample every 5 meters)
            df_sampled = df.iloc[::max(1, len(df) // 150)]
            log_entries = []

            for _, row in df_sampled.iterrows():
                d_val = float(row[depth_col]) if pd.notna(row[depth_col]) else None
                if d_val is None or d_val < 0:
                    continue
                
                gr_val = float(row[gr_col]) if gr_col and pd.notna(row[gr_col]) else None
                res_val = float(row[res_col]) if res_col and pd.notna(row[res_col]) else None
                dt_val = float(row[sonic_col]) if sonic_col and pd.notna(row[sonic_col]) else None
                rhob_val = float(row[dens_col]) if dens_col and pd.notna(row[dens_col]) else None

                # Determine formation based on depth
                formation_top = "Tipam Sandstone" if d_val < 2200 else ("Barail Formation" if d_val < 2950 else "Kopili Formation")

                log_entry = WellLog(
                    well_id=well_id,
                    depth_tvd=d_val,
                    gamma_ray=gr_val,
                    resistivity=res_val,
                    sonic=dt_val,
                    density=rhob_val,
                    formation_top=formation_top
                )
                log_entries.append(log_entry)

            if log_entries:
                db.add_all(log_entries)
                db.commit()

            return {
                "status": "success",
                "file_type": "las",
                "filename": file.filename,
                "curves_identified": [c for c in [gr_col, res_col, sonic_col, dens_col] if c is not None],
                "points_ingested": len(log_entries),
                "message": f"Successfully parsed LAS file: {len(log_entries)} well log points ingested into well_log table."
            }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/api/events/contribute")
def contribute_lesson_learned(
    payload: ContributeLessonSchema,
    db: Session = Depends(get_db)
):
    """
    Institutional Memory Two-Way Feedback Loop (SIH 2026 Core Mandate):
    Allows field engineers and operations reviewers to log lessons learned and mitigations
    from active drilling. Uses the exact same BGE-small embedding model (384 dims) as RAG search
    so the new record is immediately retrievable within the same session.
    """
    # 1. Verify well exists
    well = db.query(WellMaster).filter(WellMaster.well_id == payload.well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {payload.well_id} not found in well_master registry")

    # 2. Construct dense context text for embedding (matching ingest.py convention)
    context_str = (
        f"{payload.event_type} in {payload.formation} at {payload.depth_tvd}m TVD. "
        f"Severity: {payload.severity}. Root cause: {payload.root_cause}. "
        f"Mitigation: {payload.mitigation_applied}."
    )

    # 3. Generate embedding using the exact same model (bge-small-en-v1.5)
    try:
        embedding = get_embedding(context_str)
        # Verify 384 dimensions
        assert len(embedding) == 384, f"Expected 384 dims from bge-small-en-v1.5, got {len(embedding)}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding model generation failed: {e}")

    # 4. Insert into SyntheticEvent table
    new_event = SyntheticEvent(
        well_id=payload.well_id,
        depth_start_tvd=payload.depth_tvd,
        depth_end_tvd=payload.depth_tvd,
        formation=payload.formation,
        event_type=payload.event_type,
        severity=payload.severity.upper(),
        root_cause=payload.root_cause,
        mitigation_applied=payload.mitigation_applied,
        npt_hours=payload.npt_hours or 0.0,
        embedding=embedding
    )

    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {e}")

    return {
        "status": "success",
        "message": f"Lesson successfully committed to Institutional Memory with {len(embedding)}-dim vector embedding.",
        "event_id": new_event.id,
        "well_id": new_event.well_id,
        "embedding_dimensions": len(embedding),
        "is_immediately_searchable": True
    }
