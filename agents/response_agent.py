"""
agents/response_agent.py

Formats the final user-facing answer.
Takes the analyst's draft and the critic's assessment and produces a clean,
professional response — adding confidence caveats where appropriate.
"""

from dataclasses import dataclass
from utils.openai_helper import chat_completion
from agents.critic_agent import CriticResult

SYSTEM_PROMPT = """You are a professional enterprise communication assistant.

Your task is to format a final, polished answer for an employee asking a company policy question.

Guidelines:
- Start with a direct, clear answer to the question in 1–2 sentences.
- Follow with any relevant conditions, thresholds, or steps from the policy.
- If a caveat flag is included, add a note at the end (e.g. "Note: Some details may not be fully covered by the retrieved policy. We recommend confirming with your manager or the relevant department.")
- Use plain, professional language — no jargon, no markdown headers.
- Be concise. The answer should be easy to read in under 60 seconds.
- End with the source policy name(s) that informed this answer."""

CAVEAT_NOTE = (
    "\n\n⚠️ Note: This answer may not cover all relevant policy details. "
    "Please verify with your manager or the relevant department before taking action."
)

LOW_CONFIDENCE_NOTE = (
    "\n\n⚠️ Low Confidence: The retrieved policy sections may not fully address your question. "
    "Consider contacting the relevant policy owner directly."
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
    """
    Produce the final formatted answer for the user.

    Args:
        user_query:    Original user question.
        draft_answer:  Analyst's draft answer.
        critic_result: Quality assessment from the Critic agent.
        source_files:  Policy filenames that were searched.

    Returns:
        A ResponseResult with the polished final answer string.
    """
    if not draft_answer:
        return ResponseResult(error="No answer to format.")

    try:
        sources_str = ", ".join(source_files) if source_files else "company policy documents"
        caveat_instruction = (
            "Add a caveat note at the end of the answer."
            if critic_result.needs_caveat
            else "No caveat needed."
        )

        user_message = (
            f"USER QUESTION: {user_query}\n\n"
            f"DRAFT ANSWER:\n{draft_answer}\n\n"
            f"SOURCE DOCUMENTS: {sources_str}\n\n"
            f"CAVEAT INSTRUCTION: {caveat_instruction}\n\n"
            f"Produce the final formatted answer now."
        )

        final = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        # Append hard-coded confidence note if critic flagged low confidence
        # (belt-and-suspenders — the LLM may miss this edge case)
        if critic_result.confidence.upper() == "LOW":
            final += LOW_CONFIDENCE_NOTE
        elif critic_result.needs_caveat and CAVEAT_NOTE.strip() not in final:
            final += CAVEAT_NOTE

        return ResponseResult(final_answer=final)

    except Exception as exc:
        return ResponseResult(error=f"Response agent failed: {str(exc)}")
