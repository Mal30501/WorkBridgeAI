"""
Guardrail agent.

Runs before any LLM call. Blocks obvious prompt injection attempts,
jailbreaks, off-topic queries, and invalid input.
"""

import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|all)\s+instructions",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions|prompt)",
    r"bypass\s+(security|guardrails?|filters?|policies?)",
    r"forget\s+(everything|all\s+previous)",
    r"you\s+are\s+now\s+(a\s+)?different",
    r"pretend\s+you\s+(are|have\s+no)",
    r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+policy)",
    r"override\s+(your\s+)?(rules?|instructions?|system)",
    r"do\s+anything\s+now",
    r"developer\s+mode",
    r"\bdan\b",
    r"jailbreak",
    r"<\s*script",
    r"\{\{.*\}\}",
]

OFF_TOPIC_PATTERNS = [
    r"\b(recipe|cook|food|sport|movie|music|weather|stock\s+price|crypto)\b",
    r"\b(write\s+(me\s+)?(a\s+)?(poem|song|story|essay))\b",
    r"\b(tell\s+me\s+a\s+joke)\b",
]

MIN_QUERY_LENGTH = 8
MAX_QUERY_LENGTH = 800


@dataclass
class GuardrailResult:
    is_safe: bool
    reason: str


def run(user_query: str) -> GuardrailResult:
    """Check whether the user query is safe and relevant."""
    query = user_query.strip()

    if len(query) < MIN_QUERY_LENGTH:
        return GuardrailResult(
            is_safe=False,
            reason="Query is too short. Please ask a specific policy question.",
        )

    if len(query) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            is_safe=False,
            reason=f"Query exceeds the maximum allowed length of {MAX_QUERY_LENGTH} characters.",
        )

    query_lower = query.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return GuardrailResult(
                is_safe=False,
                reason="Potential prompt injection or system override attempt detected. Request blocked.",
            )

    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, query_lower):
            return GuardrailResult(
                is_safe=False,
                reason=(
                    "Query appears unrelated to company policy. "
                    "WorkBridge AI only answers questions about internal policy workflows."
                ),
            )

    return GuardrailResult(
        is_safe=True,
        reason="Query passed safety and relevance checks. Proceeding to planning.",
    )