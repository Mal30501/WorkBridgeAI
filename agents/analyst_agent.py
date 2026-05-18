"""
agents/analyst_agent.py

Generates a grounded answer using ONLY the retrieved policy context.
The system prompt explicitly forbids the model from using outside knowledge,
which is the core safety property of a RAG-based enterprise assistant.
"""

from dataclasses import dataclass
from utils.openai_helper import chat_completion
from agents.retriever_agent import PolicyChunk

SYSTEM_PROMPT = """You are an enterprise policy analyst assistant.

Your task is to answer the user's question using ONLY the policy text provided below.

STRICT RULES:
- Do not use any knowledge outside of the provided policy context.
- If the policy context does not contain enough information to answer confidently, say so explicitly.
- Do not speculate or infer beyond what is written in the policy.
- Cite the relevant section or rule when possible (e.g. "Per Section 1.3 of the Refund Policy...").
- Be concise but complete. A few clear sentences are better than a long vague answer.
- If the answer has conditions (e.g. dollar thresholds, approval levels), state them clearly.

Your answer will be reviewed by a critic agent before it reaches the user."""


def _build_context(chunks: list[PolicyChunk]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[Source {i}: {chunk.source_file}]")
        lines.append(chunk.content)
        lines.append("")   # blank line separator
    return "\n".join(lines)


@dataclass
class AnalystResult:
    answer: str = ""
    context_used: str = ""
    error: str = ""


def run(user_query: str, chunks: list[PolicyChunk]) -> AnalystResult:
    """
    Produce a grounded policy answer from the retrieved chunks.

    Args:
        user_query: The original question from the user.
        chunks:     Relevant policy sections returned by the Retriever agent.

    Returns:
        An AnalystResult containing the draft answer and the context that was used.
    """
    if not chunks:
        return AnalystResult(error="No context available — cannot generate an answer.")

    try:
        context = _build_context(chunks)
        user_message = (
            f"POLICY CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {user_query}\n\n"
            f"Answer the question using only the policy context above."
        )

        answer = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        return AnalystResult(answer=answer, context_used=context)

    except Exception as exc:
        return AnalystResult(error=f"Analyst agent failed: {str(exc)}")
