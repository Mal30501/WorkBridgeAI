"""
Planner agent.

Turns the user's policy question into a short retrieval and analysis plan.
"""

from dataclasses import dataclass, field

from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are a planning assistant for an enterprise policy Q&A system.

Create a short plan for answering the user's policy question.

Output ONLY a numbered list of 2-4 steps.

Good format:
1. Identify the relevant policy domain.
2. Retrieve the policy sections that mention the specific rule or threshold.
3. Check whether the user's scenario is directly covered by the policy.
4. Summarize the applicable rule clearly.

Do not answer the question itself.
Keep each step short and practical."""


@dataclass
class PlannerResult:
    steps: list[str] = field(default_factory=list)
    raw_output: str = ""
    error: str = ""


def _parse_steps(raw: str) -> list[str]:
    """Extract numbered steps from the model response."""
    steps = []

    for line in raw.splitlines():
        line = line.strip()

        if not line or not line[0].isdigit():
            continue

        if "." in line:
            step = line.split(".", 1)[1].strip()
        elif ")" in line:
            step = line.split(")", 1)[1].strip()
        else:
            step = line

        if step:
            steps.append(step)

    return steps


def run(user_query: str) -> PlannerResult:
    """Generate a short plan for retrieving and analyzing policy context."""
    try:
        raw = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Policy question: {user_query}",
        )

        steps = _parse_steps(raw)

        if not steps:
            steps = [raw.strip()]

        return PlannerResult(steps=steps, raw_output=raw)

    except Exception as exc:
        return PlannerResult(
            error=f"Planner agent failed: {exc}",
            raw_output="",
        )