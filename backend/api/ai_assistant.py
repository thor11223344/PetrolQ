import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import SyntheticEvent
from nlp.config import get_embedding
from nlp.llm_factory import (
    get_llm,
    is_llm_available,
    get_llm_status,
    detect_active_provider,
    PROVIDER_OFFLINE
)
from guardrails.guardrails_service import GuardrailsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI & LLM Services"])

class AISynthesizeRequest(BaseModel):
    query: str = Field(..., description="Engineering query or hazard scenario (e.g. 'Barail high pressure gas kick mitigation')")
    well_id: Optional[str] = Field("OIL-BAGHJAN-1", description="Reference well ID")
    depth_tvd: Optional[float] = Field(None, description="Current or target TVD in meters")
    formation: Optional[str] = Field(None, description="Geological formation name if known")
    max_records: Optional[int] = Field(5, description="Maximum historical records to retrieve as evidence")

class CitationSchema(BaseModel):
    source_file: str
    source_page: int
    well_id: Optional[str] = None
    depth_tvd: Optional[float] = None

class AISynthesizeResponse(BaseModel):
    status: str
    provider: str
    model: str
    summary: str
    recommendations: List[str]
    citations: List[CitationSchema]
    guardrail_verified: bool
    guardrail_violations: List[str]
    mode: str

@router.get("/status")
def get_ai_status():
    """
    Returns the real-time configuration status of the AI/LLM engine.
    Indicates whether Google Gemini, Anthropic Claude, OpenAI, or Ollama is active,
    or if the system is running in offline deterministic mode.
    """
    return get_llm_status()

@router.post("/synthesize", response_model=AISynthesizeResponse)
def synthesize_incident_briefing(
    payload: AISynthesizeRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesizes historical drilling intelligence and offset well incidents using the configured LLM
    (Gemini, Claude, OpenAI, or Ollama) with strict Guardrail verification.
    """
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve historical incident evidence using hybrid vector/keyword search
    events_query = db.query(SyntheticEvent)
    if payload.well_id and "OIL-" in payload.well_id:
        # Prioritize matching region or well
        pass

    all_events = events_query.all()
    
    # Generate query embedding for similarity scoring
    scored_events = []
    try:
        q_vec = get_embedding(query_text)
        from main import compute_cosine_similarity
        for ev in all_events:
            if ev.embedding:
                score = compute_cosine_similarity(q_vec, ev.embedding)
                scored_events.append((score, ev))
        scored_events.sort(key=lambda x: x[0], reverse=True)
    except Exception as e:
        logger.warning(f"Vector search failed in synthesis ({e}), using lexical fallback.")
        # Lexical fallback
        q_lower = query_text.lower()
        for ev in all_events:
            txt = f"{ev.event_type} {ev.formation} {ev.root_cause} {ev.mitigation_applied}".lower()
            score = 1.0 if any(term in txt for term in q_lower.split()) else 0.0
            scored_events.append((score, ev))
        scored_events.sort(key=lambda x: x[0], reverse=True)

    top_events = [ev for _, ev in scored_events[:payload.max_records]] if scored_events else []

    # 2. Build deterministic baseline evidence
    citations = []
    deterministic_recs = []
    evidence_lines = []

    for idx, ev in enumerate(top_events):
        source_name = f"well_{ev.well_id}_history.las"
        citations.append({
            "source_file": source_name,
            "source_page": idx + 1,
            "well_id": ev.well_id,
            "depth_tvd": ev.depth_start_tvd
        })
        if ev.mitigation_applied and ev.mitigation_applied not in deterministic_recs:
            deterministic_recs.append(ev.mitigation_applied)
        
        evidence_lines.append(
            f"[{idx+1}] Well: {ev.well_id} | Depth: {ev.depth_start_tvd}m | Formation: {ev.formation} | "
            f"Hazard: {ev.event_type} | Cause: {ev.root_cause} | Mitigation: {ev.mitigation_applied}"
        )

    evidence_context = "\n".join(evidence_lines) if evidence_lines else "No direct historical offset incident matches found."

    deterministic_evidence = {
        "confidence": "high" if len(top_events) >= 2 else "medium",
        "citations": [{"source_file": c["source_file"], "source_page": c["source_page"]} for c in citations],
        "recommended_actions": deterministic_recs[:3] if deterministic_recs else [
            "Maintain baseline drilling parameters (WOB, RPM, Flow Rate).",
            "Monitor pit levels and standpipe pressure for precursor fluctuations."
        ]
    }

    active_provider, active_model = detect_active_provider()

    # 3. LLM Generation or Offline Rule-based Fallback
    if is_llm_available():
        try:
            llm = get_llm(temperature=0.1, timeout=10.0)
            system_prompt = (
                "You are an expert Senior Drilling Superintendent and Geomechanics Engineer for Oil India Limited. "
                "Analyze the provided historical offset well evidence and synthesize an executive briefing. "
                "Rules:\n"
                "1. Base your summary strictly on the provided evidence. Cite source indices like [1], [2] when referencing events.\n"
                "2. Provide exactly 2 to 3 actionable, physically grounded engineering recommendations.\n"
                "3. Never advise automated rig shutdown or autonomous BOP control.\n"
                "Format your answer as:\n"
                "SUMMARY: <2-3 sentences>\n"
                "RECOMMENDATIONS:\n"
                "- <Recommendation 1>\n"
                "- <Recommendation 2>\n"
            )
            
            prompt_text = (
                f"Operational Query: {query_text}\n"
                f"Reference Well: {payload.well_id} | Depth: {payload.depth_tvd or 'Not specified'}m\n\n"
                f"Historical Offset Evidence:\n{evidence_context}\n\n"
                "Synthesize the briefing:"
            )

            response = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ])
            raw_text = response.content if hasattr(response, "content") else str(response)

            # Parse LLM response
            summary_part = ""
            recs_part = []
            
            if "SUMMARY:" in raw_text:
                parts = raw_text.split("RECOMMENDATIONS:")
                summary_part = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    lines = parts[1].strip().split("\n")
                    for l in lines:
                        clean_l = l.strip().lstrip("-*123456789. ")
                        if clean_l:
                            recs_part.append(clean_l)
            else:
                summary_part = raw_text.strip()
                recs_part = deterministic_recs[:3]

            llm_candidate = {
                "confidence": "high" if len(top_events) >= 2 else "medium",
                "citations": [{"source_file": c["source_file"], "source_page": c["source_page"]} for c in citations],
                "recommendations": recs_part if recs_part else deterministic_recs[:3],
                "summary": summary_part,
                "reasoning": f"Synthesized from {len(top_events)} offset incidents using {active_provider} ({active_model})."
            }

        except Exception as e:
            logger.warning(f"LLM call failed ({e}). Falling back to deterministic synthesis.")
            llm_candidate = {
                "confidence": "medium",
                "citations": [{"source_file": c["source_file"], "source_page": c["source_page"]} for c in citations],
                "recommendations": deterministic_recs[:3] if deterministic_recs else ["Perform manual crew review."],
                "summary": f"Historical offset records show {len(top_events)} relevant incidents matching query. Primary hazards include: {', '.join(set(ev.event_type for ev in top_events)) if top_events else 'General operational risk'}.",
                "reasoning": "Deterministic domain synthesis (LLM connection error fallback)."
            }
    else:
        # Fully offline deterministic synthesis
        hazard_types = list(set(ev.event_type for ev in top_events)) if top_events else ["General Drilling Hazard"]
        formations = list(set(ev.formation for ev in top_events if ev.formation))
        form_str = f" in {', '.join(formations)}" if formations else ""
        
        llm_candidate = {
            "confidence": "medium" if top_events else "low",
            "citations": [{"source_file": c["source_file"], "source_page": c["source_page"]} for c in citations],
            "recommendations": deterministic_recs[:3] if deterministic_recs else [
                "Circulate bottoms up and inspect mud properties.",
                "Review offset drilling parameters before increasing penetration rate."
            ],
            "summary": f"Identified {len(top_events)} offset well incident records{form_str}. Key historical risk patterns involve {', '.join(hazard_types[:3])}.",
            "reasoning": "Deterministic rules-based domain synthesizer (Offline Mode)."
        }

    # 4. Guardrails Verification
    val_result = GuardrailsService.validate(deterministic_evidence, llm_candidate)
    final_output = val_result["validated_response"]

    return AISynthesizeResponse(
        status="success",
        provider=active_provider,
        model=active_model,
        summary=final_output.get("summary", ""),
        recommendations=final_output.get("recommendations", []),
        citations=[CitationSchema(**c) for c in citations],
        guardrail_verified=val_result["allowed"],
        guardrail_violations=val_result.get("violations", []),
        mode="live_llm" if active_provider != PROVIDER_OFFLINE and is_llm_available() else "offline_deterministic"
    )
