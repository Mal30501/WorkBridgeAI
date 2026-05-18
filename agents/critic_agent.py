"""
Critic agent.

Reviews the analyst's draft answer against the retrieved policy context.
"""

from dataclasses import dataclass

from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are a quality assurance critic for an enterprise AI policy assistant.

Evaluate the draft answer against the source policy context.

Check:
1. GROUNDING: Is every factual claim supported by the policy context?
2. ACCURACY: Are thresholds, roles, timelines, and policy rules correct?
3. COMPLETENESS: Does the answer address the user's question?
4. CONFIDENCE: Should the system present this as HIGH, MEDIUM, or LOW confidence?

Respond ONLY in this structure:
GROUNDING: [Supported / Partially Supported / Not Supported]
ACCURACY: [Accurate / Minor Issues / Major Issues]
COMPLETENESS: [Complete / Partial / Incomplete]
CONFIDENCE: [HIGH / MEDIUM / LOW]
ISSUES: [One-line issue summary, or "None"]
RECOMMENDATION: [APPROVE / APPROVE WITH CAVEAT / REVISE]

Be brief and precise. Do not repeat the full answer or policy context."""


@dataclass
class CriticResult:
    grounding: str = ""
    accuracy: str = ""
    completeness: str = ""
    confidence: str = ""
    issues: str = ""
    recommendation: str = ""
    raw_output: str = ""
    error: str = ""

    @property
    def approved(self) -> bool:
        normalized = self.recommendation.strip().upper()
        return normalized in {"APPROVE", "APPROVE WITH CAVEAT"}

    @property
    def needs_caveat(self) -> bool:
        return self.recommendation.strip().upper() == "APPROVE WITH CAVEAT"


def _parse_critic_output(raw: str) -> dict[str, str]:
    """Parse the critic output into simple key-value fields."""
    fields = {}

    for line in raw.splitlines():
        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        fields[key.strip().upper()] = value.strip()

    return fields


def run(user_query: str, draft_answer: str, context_used: str) -> CriticResult:
    """Validate the draft answer against the retrieved policy context."""
    if not draft_answer:
        return CriticResult(error="No draft answer was provided for review.")

    try:
        user_message = (
            f"POLICY CONTEXT USED:\n{context_used}\n\n"
            f"USER QUESTION:\n{user_query}\n\n"
            f"DRAFT ANSWER TO EVALUATE:\n{draft_answer}"
        )

        raw = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        parsed = _parse_critic_output(raw)

        return CriticResult(
            grounding=parsed.get("GROUNDING", "Unknown"),
            accuracy=parsed.get("ACCURACY", "Unknown"),
            completeness=parsed.get("COMPLETENESS", "Unknown"),
            confidence=parsed.get("CONFIDENCE", "Unknown"),
            issues=parsed.get("ISSUES", "None"),
            recommendation=parsed.get("RECOMMENDATION", "REVISE"),
            raw_output=raw,
        )

    except Exception as exc:
        return CriticResult(error=f"Critic agent failed: {exc}")