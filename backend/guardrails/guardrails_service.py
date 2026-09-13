import re
from typing import Dict, Any, List

CONFIDENCE_RANKS = {"insufficient": 0, "low": 1, "medium": 2, "high": 3}

UNSAFE_COMMAND_PATTERNS = [
    r"\b(auto-driller|bop|blowout preventer|shut down|shutdown|kill pump|actuate)\b",
    r"\b(set wob to 0|set rpm to 0|halt rig|trigger emergency|override driller)\b",
    r"\b(command control system|direct rig action|execute auto)\b"
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"system prompt override",
    r"you are now (an )?unrestricted",
    r"reveal (api )?key",
    r"admin mode",
    r"bypass guardrails"
]


class GuardrailsService:
    """Validates LLM output against deterministic ground truth before it reaches the user."""

    @classmethod
    def validate(cls, deterministic_result: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[str] = []

        # 1. Confidence can't be inflated beyond what the deterministic system computed
        det_confidence = str(deterministic_result.get("confidence", "insufficient")).lower()
        llm_confidence = str(llm_result.get("confidence", "insufficient")).lower()
        if CONFIDENCE_RANKS.get(llm_confidence, 0) > CONFIDENCE_RANKS.get(det_confidence, 0):
            violations.append(f"Confidence upgrade blocked: LLM claimed '{llm_confidence}' vs deterministic '{det_confidence}'.")

        # 2. Citation fabrication check — every cited source must exist in the real evidence set
        valid_sources = {(c.get("source_file"), c.get("source_page")) for c in deterministic_result.get("citations", [])}
        for c in llm_result.get("citations", []):
            key = (c.get("source_file"), c.get("source_page"))
            if key not in valid_sources:
                violations.append(f"Fabricated citation blocked: {key}")

        # 3. Block any recommendation suggesting autonomous physical rig control
        for rec in llm_result.get("recommendations", []):
            for pattern in UNSAFE_COMMAND_PATTERNS:
                if re.search(pattern, str(rec), re.IGNORECASE):
                    violations.append(f"Unsafe autonomous-control recommendation blocked: '{rec}'")
                    break

        # 4. Prompt injection detection across all free-text LLM fields
        combined_text = " ".join([
            str(llm_result.get("summary", "")),
            str(llm_result.get("reasoning", "")),
            " ".join(str(r) for r in llm_result.get("recommendations", []))
        ])
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                violations.append("Prompt injection pattern detected in LLM output.")
                break

        allowed = len(violations) == 0
        return {
            "allowed": allowed,
            "violations": violations,
            "validated_response": llm_result if allowed else cls._fallback(deterministic_result),
        }

    @classmethod
    def _fallback(cls, deterministic_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Guardrail intervention: reverted to deterministic result due to validation failure.",
            "confidence": deterministic_result.get("confidence", "insufficient"),
            "recommendations": deterministic_result.get("recommended_actions", []),
            "citations": deterministic_result.get("citations", []),
        }
