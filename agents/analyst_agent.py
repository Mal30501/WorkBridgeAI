"""
Analyst agent.

Generates a policy answer using only the retrieved policy context.
"""

from dataclasses import dataclass

from agents.retriever_agent import PolicyChunk
from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are an enterprise policy analyst assistant.

Answer the user's question using ONLY the policy context provided.

Rules:
- Do not use outside knowledge.
- If the provided context is not enough, say that clearly.
- Do not speculate beyond the policy text.
- Mention the relevant policy section or rule when available.
- Keep the answer concise, practical, and easy for an employee to understand.
- If thresholds, approvals, timelines, or escalation rules apply, state them clearly.

Your answer will be checked by a critic agent before it is shown to the user."""


@dataclass
class AnalystResult:
    answer: str = ""
    context_used: str = ""
    error: str = ""


def _build_context(chunks: list[PolicyChunk]) -> str:
    """Format retrieved chunks for the LLM prompt."""
    lines = []

    for index, chunk in enumerate(chunks, 1):
        lines.append(f"[Source {index}: {chunk.source_file}]")
        lines.append(chunk.content)
        lines.append("")

    return "\n".join(lines)


def run(user_query: str, chunks: list[PolicyChunk]) -> AnalystResult:
    """Create a grounded draft answer from retrieved policy chunks."""
    if not chunks:
        return AnalystResult(error="No policy context was found, so an answer cannot be generated.")

    try:
        context = _build_context(chunks)

        user_message = (
            f"POLICY CONTEXT:\n{context}\n\n"
            f"USER QUESTION:\n{user_query}\n\n"
            "Answer the question using only the policy context above."
        )

        answer = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        return AnalystResult(answer=answer, context_used=context)

    except Exception as exc:
        return AnalystResult(error=f"Analyst agent failed: {exc}")