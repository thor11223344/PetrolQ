import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Import the configuration we created earlier
from backend.nlp.config import LLM_API_KEY, LLM_ENDPOINT, LLM_MODEL_NAME

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

def _get_llm():
    """
    Initialize the LLM. 
    ChatOpenAI is highly compatible with both official OpenAI APIs and local Ollama instances.
    """
    return ChatOpenAI(
        model=LLM_MODEL_NAME,
        base_url=LLM_ENDPOINT if LLM_ENDPOINT else None,
        api_key=LLM_API_KEY,
        temperature=0.0  # Use zero temperature for deterministic, factual extraction
    )

def extract_incidents_from_text(text: str) -> List[DrillingIncidentSchema]:
    """
    Extracts structured drilling incident data from a single text chunk.
    """
    if not text.strip():
        return []

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
        result: IncidentExtractionResult = chain.invoke({"text": text})
        
        return result.incidents if result else []
        
    except Exception as e:
        logger.error(f"Failed to extract incidents from text: {e}")
        return []

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
