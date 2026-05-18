"""
agents/planner_agent.py

Breaks the user's question into a small set of actionable steps.
This gives the rest of the pipeline (retrieval, analysis, critique) a clear
goal to work toward, and makes the agent's reasoning visible in the UI trace.
"""

from dataclasses import dataclass, field
from utils.openai_helper import chat_completion

SYSTEM_PROMPT = """You are a planning assistant for an enterprise policy Q&A system.

Your job is to analyse the user's policy question and produce a short, structured plan.

Output format — respond ONLY with a numbered list of 2–4 steps, like:
1. Identify which policy domain(s) are relevant (refunds, PII, escalation, etc.)
2. Retrieve sections from the relevant policy document(s)
3. Check whether the specific scenario (dollar amount, data type, etc.) is addressed
4. Summarise the applicable rule clearly for the user

Do not answer the question itself. Only plan how to answer it.
Keep each step to one concise sentence. No extra commentary."""


@dataclass
class PlannerResult:
    steps: list[str] = field(default_factory=list)
    raw_output: str = ""
    error: str = ""


def run(user_query: str) -> PlannerResult:
    """
    Generate a structured retrieval and analysis plan for the given query.

    Returns a PlannerResult with a list of plain-text steps.
    """
    try:
        raw = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Policy question: {user_query}"
        )

        # Parse numbered lines into a clean list
        steps = []
        for line in raw.splitlines():
            line = line.strip()
            # Accept lines starting with a digit and a period/dot
            if line and line[0].isdigit():
                # Strip the leading "1. " prefix
                cleaned = line.split(".", 1)[-1].strip()
                if cleaned:
                    steps.append(cleaned)

        if not steps:
            # Fallback: treat entire response as a single step
            steps = [raw.strip()]

        return PlannerResult(steps=steps, raw_output=raw)

    except Exception as exc:
        return PlannerResult(
            error=f"Planner agent failed: {str(exc)}",
            raw_output="",
        )
