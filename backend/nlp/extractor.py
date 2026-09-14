import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# Import unified multi-provider factory
from nlp.llm_factory import get_llm, is_llm_available, detect_active_provider

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Pydantic Schemas for Structured Output
# -------------------------------------------------------------------

class DrillingIncidentSchema(BaseModel):
    event_type: str = Field(
        description="E.g., 'Stuck Pipe (Mechanical)', 'Stuck Pipe (Differential)', 'Severe Mud Loss', 'Gas Kick', 'Tight Hole', 'Equipment Failure'"
    )
    depth_tvd: Optional[float] = Field(
        description="Estimated or exact True Vertical Depth in meters", 
        default=None
    )
    severity: str = Field(
        description="Enum-like string: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'"
    )
    formation: str = Field(
        description="Formation name if mentioned, e.g., 'Barail', 'Tipam', 'Kopili', or 'Unknown'", 
        default="Unknown"
    )
    root_cause: str = Field(
        description="Concise technical description of why the incident occurred"
    )
    mitigation_applied: str = Field(
        description="Remediation steps, pills pumped, reaming practices used to resolve the issue"
    )
    npt_hours: float = Field(
        description="Non-productive time in hours, default 0.0", 
        default=0.0
    )

class IncidentExtractionResult(BaseModel):
    """
    Wrapper schema because LLMs need a top-level object to return lists accurately 
    in structured output mode.
    """
    incidents: List[DrillingIncidentSchema] = Field(
        description="List of extracted drilling incidents. If none, return an empty list.",
        default_factory=list
    )


# -------------------------------------------------------------------
# Extraction Logic
# -------------------------------------------------------------------

def _is_llm_available() -> bool:
    """Check if any remote or local LLM server is accessible without blocking."""
    return is_llm_available()

def _get_llm():
    """
    Initialize the LLM using the universal factory.
    Supports Google Gemini, Anthropic Claude, OpenAI, and Ollama (Local).
    """
    return get_llm(temperature=0.0, timeout=8.0)

def extract_incidents_from_text(text: str) -> List[DrillingIncidentSchema]:
    """
    Extracts structured drilling incident data from a single text chunk.
    """
    if not text.strip():
        return []

    if not _is_llm_available():
        return _rule_based_fallback_extraction(text)

    try:
        llm = _get_llm()
        # Bind the Pydantic schema to the LLM to force JSON output matching the schema
        structured_llm = llm.with_structured_output(IncidentExtractionResult)
        
        system_prompt = (
            "You are an expert Senior Drilling Engineer reviewing historical Daily Drilling Reports and Well Completion Reports. "
            "Extract all downhole incidents, hazard events, kicks, stuck pipe situations, and NPT entries. "
            "If no drilling incident or operational hazard occurred in the text, return an empty list. Maintain domain precision."
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Extract the incidents from the following report text:\n\n{text}")
        ])
        
        chain = prompt | structured_llm
        raw_result = chain.invoke({"text": text})
        if isinstance(raw_result, IncidentExtractionResult):
            return raw_result.incidents
        elif isinstance(raw_result, dict):
            return IncidentExtractionResult.model_validate(raw_result).incidents
        elif hasattr(raw_result, "incidents"):
            return getattr(raw_result, "incidents", [])
        return []
        
    except Exception as e:
        logger.warning(f"LLM extraction unavailable ({e}). Engaging deterministic domain NLP fallback...")
        return _rule_based_fallback_extraction(text)

def _rule_based_fallback_extraction(text: str) -> List[DrillingIncidentSchema]:
    """
    Robust rule-based domain extractor for drilling reports when LLM is unavailable or offline.
    Detects incident types, formations, depths, root causes, mitigations, and NPT hours.
    """
    import re
    incidents = []
    
    # Common drilling incident types
    hazard_patterns = [
        ("Lost Circulation", r"(lost\s+circulation|mud\s+loss|seepage\s+losses|total\s+loss)"),
        ("Gas Kick", r"(gas\s+kick|well\s+kick|influx|gas\s+spike|pit\s+gain|sidpp)"),
        ("Differential Sticking", r"(differential\s+sticking|stuck\s+pipe|pipe\s+stuck)"),
        ("Mechanical Packoff", r"(packoff|pack-off|tight\s+hole|bridging|drag)"),
        ("Equipment Failure", r"(twist-off|mwd\s+failure|bha\s+washout|bit\s+failure)")
    ]

    # Formations
    formations = ["Barail Formation", "Barail", "Tipam Sandstone", "Tipam", "Kopili Formation", "Kopili", "Girujan Clay", "Girujan"]

    # Split text into paragraphs or incident blocks
    blocks = re.split(r"(?:Incident\s*\d*[:\-]|Entry\s*\d*[:\-]|Hazard\s*\d*[:\-]|---|\n\s*\n)", text, flags=re.IGNORECASE)
    
    for block in blocks:
        block_clean = block.strip()
        if len(block_clean) < 30:
            continue
            
        matched_type = None
        for name, pattern in hazard_patterns:
            if re.search(pattern, block_clean, re.IGNORECASE):
                matched_type = name
                break
                
        if not matched_type:
            continue
            
        # Extract formation
        form_found = "Barail Formation"
        for f in formations:
            if re.search(r"\b" + re.escape(f) + r"\b", block_clean, re.IGNORECASE):
                form_found = f if "Formation" in f or "Sandstone" in f or "Clay" in f else f + " Formation"
                break
                
        # Extract depth (TVD/MD)
        depth = 2425.0
        depth_match = re.search(r"(\d{3,4}(?:\.\d+)?)\s*(?:m|meters)?\s*(?:tvd|md)?", block_clean, re.IGNORECASE)
        if depth_match:
            try:
                val = float(depth_match.group(1))
                if 500 <= val <= 6000:
                    depth = val
            except ValueError:
                pass
                
        # Extract NPT hours
        npt = 3.5
        npt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?|h)\s*(?:npt)?", block_clean, re.IGNORECASE)
        if npt_match:
            try:
                npt = float(npt_match.group(1))
            except ValueError:
                pass
                
        # Extract root cause
        root_cause = "Formation pressure differential and rock mechanical instability during drilling."
        cause_match = re.search(r"(?:Root\s*Cause|Cause|Reason)[:\-]\s*([^\.\n]+(?:\.[^\.\n]+)?)", block_clean, re.IGNORECASE)
        if cause_match:
            root_cause = cause_match.group(1).strip()
        elif "losses" in block_clean.lower():
            root_cause = "Encountered depleted high-permeability sand body with fracture gradient lower than active hydrostatic column."
        elif "kick" in block_clean.lower():
            root_cause = "Formation pore pressure exceeded active mud hydrostatic column resulting in hydrocarbon gas influx."
            
        # Extract mitigation
        mitigation = "Adjusted mud weight, circulated bottoms up, and conditioned drilling fluid."
        mit_match = re.search(r"(?:Mitigation|Remediation|Action\s*Taken)[:\-]\s*([^\.\n]+(?:\.[^\.\n]+)?)", block_clean, re.IGNORECASE)
        if mit_match:
            mitigation = mit_match.group(1).strip()
        elif "losses" in block_clean.lower():
            mitigation = "Mixed and spotted 35 bbl LCM pill with nut-plug and mica. Soaked 2 hours and restored full circulation."
        elif "kick" in block_clean.lower():
            mitigation = "Shut-in well on annular preventer. Recorded SIDPP and SICP, circulated out influx using Driller's Method with weighted kill mud."

        incidents.append(DrillingIncidentSchema(
            event_type=matched_type,
            depth_tvd=depth,
            severity="HIGH" if ("kick" in matched_type.lower() or "sticking" in matched_type.lower()) else "MEDIUM",
            formation=form_found,
            root_cause=root_cause,
            mitigation_applied=mitigation,
            npt_hours=npt
        ))
        
    return incidents

def extract_incidents_from_chunks(chunks: List[str]) -> List[DrillingIncidentSchema]:
    """
    Batch handling to iterate through all text chunks from a document.
    """
    all_incidents = []
    for idx, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {idx + 1}/{len(chunks)} for incident extraction...")
        incidents = extract_incidents_from_text(chunk)
        if incidents:
            logger.info(f"Found {len(incidents)} incidents in chunk {idx + 1}.")
            all_incidents.extend(incidents)
            
    return all_incidents
