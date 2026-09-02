import argparse
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models import SyntheticEvent
from nlp.parser import DrillingReportParser
from nlp.extractor import extract_incidents_from_chunks
from nlp.config import get_embedding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_report(pdf_path: str, well_id: str, db_session: Session):
    """
    Parses a drilling report, extracts incidents via LLM, generates embeddings, 
    and saves them to the PostgreSQL database.
    """
    logger.info(f"Starting ingestion for {pdf_path} (Well ID: {well_id})")
    
    # 1. Parse the PDF
    parser = DrillingReportParser()
    raw_text, ocr_triggered = parser.extract_text_and_tables(pdf_path)
    
    if not raw_text:
        logger.error(f"Failed to extract any text from {pdf_path}. Exiting ingestion.")
        return {
            "status": "error",
            "message": "No readable text could be extracted from PDF",
            "ocr_triggered": ocr_triggered,
            "extracted_count": 0,
            "events": []
        }
        
    # 2. Chunk the text
    chunks = parser.create_operational_chunks(raw_text)
    logger.info(f"Generated {len(chunks)} chunks for LLM extraction.")
    
    # 3. Extract incidents from chunks
    incidents = extract_incidents_from_chunks(chunks)
    logger.info(f"Extracted {len(incidents)} total incidents from the document.")
    
    # 4. Process each incident
    events_to_insert = []
    extracted_summary = []
    for event in incidents:
        # Construct dense context string for optimal semantic search
        context_str = f"{event.event_type} in {event.formation} at {event.depth_tvd}m TVD. Root cause: {event.root_cause}. Mitigation: {event.mitigation_applied}"
        
        # Generate vector embedding
        try:
            embedding = get_embedding(context_str)
        except Exception as e:
            logger.error(f"Failed to generate embedding for context: {e}")
            continue
            
        # Map to SQLAlchemy Model
        # Note: mapping single depth_tvd to both start and end for point-in-time incidents.
        db_event = SyntheticEvent(
            well_id=well_id,
            depth_start_tvd=event.depth_tvd,
            depth_end_tvd=event.depth_tvd, 
            formation=event.formation,
            event_type=event.event_type,
            severity=event.severity,
            root_cause=event.root_cause,
            mitigation_applied=event.mitigation_applied,
            npt_hours=event.npt_hours,
            embedding=embedding
        )
        events_to_insert.append(db_event)
        extracted_summary.append({
            "event_type": event.event_type,
            "formation": event.formation,
            "depth_tvd": event.depth_tvd,
            "severity": event.severity,
            "root_cause": event.root_cause,
            "mitigation_applied": event.mitigation_applied,
            "npt_hours": event.npt_hours
        })
        
    # 5. Insert and commit to PostgreSQL
    if events_to_insert:
        try:
            db_session.add_all(events_to_insert)
            db_session.commit()
            logger.info(f"Successfully committed {len(events_to_insert)} events to the database.")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database insertion failed. Rollback triggered: {e}")
            raise e
    else:
        logger.info("No valid events found to ingest.")

    return {
        "status": "success",
        "ocr_triggered": ocr_triggered,
        "extracted_count": len(events_to_insert),
        "events": extracted_summary
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest drilling report PDF and extract structured NLP incidents.")
    parser.add_argument("--file", type=str, required=True, help="Path to the PDF file")
    parser.add_argument("--well_id", type=str, required=True, help="Well ID associated with the report")
    
    args = parser.parse_args()
    
    # Instantiate DB session and run
    db = SessionLocal()
    try:
        ingest_report(args.file, args.well_id, db)
    finally:
        db.close()
