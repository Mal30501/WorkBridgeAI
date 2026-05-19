"""
Analyst agent.

Generates a policy answer using only the retrieved policy context.
Handles partial matches with an enterprise-safe fallback rather than hallucinating.
"""

from dataclasses import dataclass

from agents.retriever_agent import PolicyChunk
from utils.openai_helper import chat_completion


SYSTEM_PROMPT = """You are an enterprise policy analyst assistant.

Answer the employee's question using ONLY the policy context provided.

Rules:
- Do not use outside knowledge or assumptions beyond what the policy text states.
- Mention the relevant policy section or rule when available.
- If thresholds, approval levels, timelines, or escalation rules apply, state them explicitly.
- Keep the answer concise and practical for an employee to act on.
- If the context partially addresses the question but does not fully cover it, say:
  "I could not find a directly matching policy section, but based on related company guidance..." 
  and summarize what the related context does say. Do NOT fabricate details.
- If the context is entirely unrelated to the question, say clearly that the topic is not
  covered in the available policy documents and suggest the employee contact HR, their manager,
  or the relevant department for guidance.

Your answer will be reviewed by a critic agent before it reaches the employee."""


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


def run(user_query: str, chunks: list[PolicyChunk], planner_domain: str = "") -> AnalystResult:
    """Create a grounded draft answer from retrieved policy chunks."""
    if not chunks:
        return AnalystResult(
            error="No policy context was found, so an answer cannot be generated."
        )

    try:
        context = _build_context(chunks)

        domain_hint = (
            f"INFERRED POLICY DOMAIN: {planner_domain}\n\n" if planner_domain else ""
        )

        user_message = (
            f"{domain_hint}"
            f"POLICY CONTEXT:\n{context}\n\n"
            f"EMPLOYEE QUESTION:\n{user_query}\n\n"
            "Answer the question using only the policy context above."
        )

        answer = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
        )

        return AnalystResult(answer=answer, context_used=context)

    except Exception as exc:
        return AnalystResult(error=f"Analyst agent failed: {exc}")
