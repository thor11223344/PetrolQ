import argparse
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models import SyntheticEvent, WellMaster
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
    
    # 4. Process each incident and run LLM Guardrails Validator
    import os
    from guardrails.guardrails_service import GuardrailsService

    # Base deterministic evidence context from PDF metadata
    pdf_filename = os.path.basename(pdf_path)
    deterministic_evidence = {
        "confidence": "medium",
        "citations": [{"source_file": pdf_filename, "source_page": 1}],
        "recommended_actions": [ev.mitigation_applied for ev in incidents if ev.mitigation_applied]
    }

    events_to_insert = []
    extracted_summary = []
    guardrail_violations = []

    for event in incidents:
        # Validate individual incident recommendation against unsafe physical control / prompt injection
        llm_candidate = {
            "confidence": "medium",
            "citations": [{"source_file": pdf_filename, "source_page": 1}],
            "recommendations": [event.mitigation_applied] if event.mitigation_applied else [],
            "summary": event.root_cause or "",
            "reasoning": event.event_type or ""
        }
        val_result = GuardrailsService.validate(deterministic_evidence, llm_candidate)
        
        mitigation_final = event.mitigation_applied
        if not val_result["allowed"]:
            logger.warning(f"Guardrail violation blocked during extraction: {val_result['violations']}")
            guardrail_violations.extend(val_result["violations"])
            # Apply safe validated response fallback
            fallback_rec = val_result["validated_response"].get("recommendations", [])
            mitigation_final = fallback_rec[0] if fallback_rec else "Advisory intervention: manual drilling crew assessment required."

        # Construct dense context string for optimal semantic search
        context_str = f"{event.event_type} in {event.formation} at {event.depth_tvd}m TVD. Root cause: {event.root_cause}. Mitigation: {mitigation_final}"
        
        # Generate vector embedding
        try:
            embedding = get_embedding(context_str)
        except Exception as e:
            logger.error(f"Failed to generate embedding for context: {e}")
            continue
            
        # Assign the 'dd_report' provenance tag for user-uploaded extraction
        provenance_tag = "dd_report"

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
            mitigation_applied=mitigation_final,
            npt_hours=event.npt_hours,
            embedding=embedding,
            data_source=provenance_tag
        )
        events_to_insert.append(db_event)
        extracted_summary.append({
            "well_id": well_id,
            "data_source": provenance_tag,
            "event_type": event.event_type,
            "formation": event.formation,
            "depth_tvd": event.depth_tvd,
            "severity": event.severity,
            "root_cause": event.root_cause,
            "mitigation_applied": mitigation_final,
            "npt_hours": event.npt_hours,
            "guardrail_verified": val_result["allowed"]
        })
        
    # 5. Insert and commit to PostgreSQL (with resilient offline cache fallback)
    if events_to_insert:
        try:
            db_session.add_all(events_to_insert)
            db_session.commit()
            logger.info(f"Successfully committed {len(events_to_insert)} events to the database.")
        except Exception as e:
            db_session.rollback()
            logger.warning(f"Database insertion skipped (offline or unreachable DB): {e}. Saving to local offline cache.")
            try:
                import json
                cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "offline_ingested_events.json")
                existing = []
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                existing.extend(extracted_summary)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2)
            except Exception as cache_err:
                logger.warning(f"Could not write offline event cache: {cache_err}")
    else:
        logger.info("No valid events found to ingest.")

    return {
        "status": "success",
        "ocr_triggered": ocr_triggered,
        "extracted_count": len(extracted_summary),
        "events": extracted_summary,
        "guardrail_verified": len(guardrail_violations) == 0,
        "guardrail_violations": guardrail_violations
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
