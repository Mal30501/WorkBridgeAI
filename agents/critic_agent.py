"""
agents/critic_agent.py

Reviews the Analyst's draft answer against the retrieved policy context.
Flags hallucinations, unsupported claims, or low-confidence responses
so the Final Response Agent can adjust tone and add appropriate caveats.
"""

from dataclasses import dataclass
from utils.openai_helper import chat_completion

SYSTEM_PROMPT = """You are a quality assurance critic for an enterprise AI policy assistant.

Your job is to evaluate a draft answer against the source policy context that was used to generate it.

You must assess:
1. GROUNDING: Is every factual claim in the answer directly supported by the policy context?
2. ACCURACY: Are dollar amounts, roles, thresholds, and rules stated correctly?
3. COMPLETENESS: Does the answer address all parts of the user's question?
4. CONFIDENCE: How confident should we be in this answer? (HIGH / MEDIUM / LOW)

Output format — respond ONLY with this structure:
GROUNDING: [Supported / Partially Supported / Not Supported]
ACCURACY: [Accurate / Minor Issues / Major Issues]
COMPLETENESS: [Complete / Partial / Incomplete]
CONFIDENCE: [HIGH / MEDIUM / LOW]
ISSUES: [One-line description of any specific problems found, or "None"]
RECOMMENDATION: [APPROVE / APPROVE WITH CAVEAT / REVISE]

Be brief and precise. Do not reproduce the answer or context."""


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
        return "APPROVE" in self.recommendation   # catches both APPROVE and APPROVE WITH CAVEAT

    @property
    def needs_caveat(self) -> bool:
        return self.recommendation == "APPROVE WITH CAVEAT"


def _parse_critic_output(raw: str) -> dict[str, str]:
    """Parse the structured critic output into a key-value dict."""
    fields = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().upper()] = value.strip()
    return fields


def run(user_query: str, draft_answer: str, context_used: str) -> CriticResult:
    """
    Validate the draft answer against the retrieved policy context.

    Args:
        user_query:    The original user question.
        draft_answer:  The Analyst agent's proposed answer.
        context_used:  The raw policy text that was passed to the Analyst.

    Returns:
        A CriticResult with structured quality fields and an overall recommendation.
    """
    if not draft_answer:
        return CriticResult(error="No draft answer to critique.")

    try:
        user_message = (
            f"POLICY CONTEXT USED:\n{context_used}\n\n"
            f"USER QUESTION: {user_query}\n\n"
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
        return CriticResult(error=f"Critic agent failed: {str(exc)}")
