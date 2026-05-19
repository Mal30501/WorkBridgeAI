"""
Response agent.

Formats the final answer for the employee and adds caveats when needed.
"""

from dataclasses import dataclass

from agents.critic_agent import CriticResult
from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are a professional enterprise communication assistant.

Format the final answer for an employee asking a company policy question.

Guidelines:
- Start with a direct answer.
- Keep the response concise and readable.
- Include important thresholds, approval levels, timelines, or escalation rules.
- Use plain professional language.
- Do not add unsupported details.
- End by naming the source policy document(s).
- Do not use markdown headings."""


CAVEAT_NOTE = (
    "\n\n⚠️ Note: Some details may not be fully covered by the retrieved policy context. "
    "Please verify with your manager or the relevant department before taking action."
)

LOW_CONFIDENCE_NOTE = (
    "\n\n⚠️ Low Confidence: The retrieved policy sections may not fully address this question. "
    "Please consult the relevant policy owner before relying on this answer."
)


@dataclass
class ResponseResult:
    final_answer: str = ""
    error: str = ""


def run(
    user_query: str,
    draft_answer: str,
    critic_result: CriticResult,
    source_files: list[str],
) -> ResponseResult:
    """Create the final user-facing response."""
    if not draft_answer:
        return ResponseResult(error="No answer was available to format.")

    try:
        sources = ", ".join(source_files) if source_files else "company policy documents"

        caveat_instruction = (
            "Add a brief caution note because the critic recommended a caveat."
            if critic_result.needs_caveat
            else "No caution note is needed unless the answer itself clearly requires one."
        )

        user_message = (
            f"USER QUESTION:\n{user_query}\n\n"
            f"DRAFT ANSWER:\n{draft_answer}\n\n"
            f"SOURCE DOCUMENTS:\n{sources}\n\n"
            f"CRITIC CONFIDENCE:\n{critic_result.confidence}\n\n"
            f"CRITIC RECOMMENDATION:\n{critic_result.recommendation}\n\n"
            f"CAVEAT INSTRUCTION:\n{caveat_instruction}\n\n"
            "Format the final answer now."
        )

        final_answer = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        if critic_result.confidence.upper() == "LOW":
            final_answer += LOW_CONFIDENCE_NOTE
        elif critic_result.needs_caveat and "verify" not in final_answer.lower():
            final_answer += CAVEAT_NOTE

        return ResponseResult(final_answer=final_answer)

    except Exception as exc:
        return ResponseResult(error=f"Response agent failed: {exc}")