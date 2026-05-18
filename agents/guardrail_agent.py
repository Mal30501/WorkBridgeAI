"""
agents/guardrail_agent.py

First line of defence: validates user input before it reaches any other agent.
Detects prompt injection attempts, jailbreak phrases, and off-topic requests.
"""

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Patterns that indicate an attempted prompt injection or system override.
# Keep this list minimal but meaningful — real enterprise guardrails are
# similarly focused on known attack vectors rather than trying to catch everything.
# ---------------------------------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|all)\s+instructions",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions|prompt)",
    r"bypass\s+(security|guardrails?|filters?|policies?)",
    r"forget\s+(everything|all\s+previous)",
    r"you\s+are\s+now\s+(a\s+)?different",
    r"pretend\s+you\s+(are|have\s+no)",
    r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+policy)",   # allow "act as a policy assistant"
    r"override\s+(your\s+)?(rules?|instructions?|system)",
    r"do\s+anything\s+now",  # "DAN" style attacks
    r"developer\s+mode",
    r"jailbreak",
    r"<\s*script",           # XSS-style injection
    r"\{\{.*\}\}",           # Template injection
]

# Topics that are clearly unrelated to enterprise policy queries.
OFF_TOPIC_PATTERNS = [
    r"\b(recipe|cook|food|sport|movie|music|weather|stock\s+price|crypto)\b",
    r"\b(write\s+(me\s+)?(a\s+)?(poem|song|story|essay))\b",
    r"\b(tell\s+me\s+a\s+joke)\b",
]

MIN_QUERY_LENGTH = 8   # Characters — reject trivially short inputs
MAX_QUERY_LENGTH = 800 # Characters — reject excessively long inputs


@dataclass
class GuardrailResult:
    is_safe: bool
    reason: str   # Human-readable explanation shown in the UI trace


def run(user_query: str) -> GuardrailResult:
    """
    Evaluate the user query for safety and relevance.

    Returns a GuardrailResult indicating whether the query is safe to process
    and a plain-text reason that will appear in the agent trace panel.
    """

    # 1. Length checks
    if len(user_query.strip()) < MIN_QUERY_LENGTH:
        return GuardrailResult(
            is_safe=False,
            reason="Query is too short. Please ask a specific policy question."
        )
    if len(user_query) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            is_safe=False,
            reason=f"Query exceeds the maximum allowed length of {MAX_QUERY_LENGTH} characters."
        )

    query_lower = user_query.lower()

    # 2. Prompt injection / jailbreak detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return GuardrailResult(
                is_safe=False,
                reason=(
                    f"Potential prompt injection detected. "
                    f"Matched pattern: '{pattern}'. Request blocked."
                )
            )

    # 3. Off-topic detection
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, query_lower):
            return GuardrailResult(
                is_safe=False,
                reason=(
                    "Query appears unrelated to company policy. "
                    "PolicyPilot only answers questions about internal company policies."
                )
            )

    # 4. Passed all checks
    return GuardrailResult(
        is_safe=True,
        reason="Query passed all safety and relevance checks. Proceeding to planning."
    )
