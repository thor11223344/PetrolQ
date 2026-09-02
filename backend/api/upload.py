from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
import os
import shutil
import uuid
from database import get_db
from sqlalchemy.orm import Session
from nlp.ingest import ingest_report

router = APIRouter()

@router.post("/api/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    well_id: str = Form(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # Save file to disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Ingest report using existing pipeline
        # This parses PDF with fitz/pdfplumber, extracts via LLM, embeds with sentence-transformers, and saves to pgvector
        ingest_report(temp_file_path, well_id, db)
        
        return {"status": "success", "message": f"Successfully parsed and ingested {file.filename}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
