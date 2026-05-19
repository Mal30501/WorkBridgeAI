"""
Planner agent.

Turns the user's policy question into a short retrieval and analysis plan.
Infers the likely policy domain from the question before planning.
"""

from dataclasses import dataclass, field

from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are a planning assistant for an enterprise policy Q&A system.

Before creating a plan, infer the most likely policy domain from the employee's question.
Common domains include: refunds, PII and data privacy, case escalation, PTO and leave, expense reimbursement, business travel, remote work, and equipment.

Then create a short, focused plan for answering the question.

Output ONLY in this format:
DOMAIN: [inferred policy domain, e.g. "PTO and Leave Policy" or "Expense Reimbursement Policy"]
PLAN:
1. [step]
2. [step]
3. [step]

Rules:
- Infer the domain even when the question is indirect or conversational (e.g. "Can I take next Friday off?" → PTO and Leave Policy).
- Keep each plan step short and practical.
- Do not answer the question itself.
- 2–4 steps is sufficient."""


@dataclass
class PlannerResult:
    domain: str = ""
    steps: list[str] = field(default_factory=list)
    raw_output: str = ""
    error: str = ""


def _parse_output(raw: str) -> tuple[str, list[str]]:
    """Extract domain and numbered steps from the model response."""
    domain = ""
    steps = []
    in_plan = False

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("DOMAIN:"):
            domain = line.split(":", 1)[1].strip()
            continue

        if line.upper().startswith("PLAN:"):
            in_plan = True
            continue

        if in_plan and line and line[0].isdigit():
            sep = "." if "." in line else ")" if ")" in line else None
            if sep:
                step = line.split(sep, 1)[1].strip()
            else:
                step = line
            if step:
                steps.append(step)

    return domain, steps


def run(user_query: str) -> PlannerResult:
    """Generate a domain-aware plan for retrieving and analyzing policy context."""
    try:
        raw = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Employee question: {user_query}",
        )

        domain, steps = _parse_output(raw)

        if not steps:
            steps = [raw.strip()]

        return PlannerResult(domain=domain, steps=steps, raw_output=raw)

    except Exception as exc:
        return PlannerResult(
            error=f"Planner agent failed: {exc}",
            raw_output="",
        )
