"""
Retriever agent.

Searches local policy files and returns the most relevant policy chunks.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


POLICIES_DIR = Path(__file__).parent.parent / "policies"

CHUNK_SIZE = 6
CHUNK_OVERLAP = 2
TOP_K = 4
MIN_SCORE = 1

KEYWORD_FILE_HINTS: dict[str, list[str]] = {
    "refund": ["refund_policy.txt"],
    "credit": ["refund_policy.txt"],
    "reimburse": ["refund_policy.txt"],
    "payment": ["refund_policy.txt"],
    "money": ["refund_policy.txt"],

    "pii": ["pii_policy.txt"],
    "personal": ["pii_policy.txt"],
    "ssn": ["pii_policy.txt"],
    "social security": ["pii_policy.txt"],
    "privacy": ["pii_policy.txt"],
    "sensitive": ["pii_policy.txt"],
    "customer data": ["pii_policy.txt"],

    "escalat": ["escalation_policy.txt"],
    "compliance": ["escalation_policy.txt"],
    "legal": ["escalation_policy.txt"],
    "fraud": ["escalation_policy.txt", "refund_policy.txt"],
    "breach": ["pii_policy.txt", "escalation_policy.txt"],
    "ticket": ["escalation_policy.txt", "pii_policy.txt"],
    "gdpr": ["pii_policy.txt", "escalation_policy.txt"],
    "ccpa": ["pii_policy.txt", "escalation_policy.txt"],
}


@dataclass
class PolicyChunk:
    source_file: str
    content: str
    score: int


@dataclass
class RetrieverResult:
    chunks: list[PolicyChunk] = field(default_factory=list)
    files_searched: list[str] = field(default_factory=list)
    error: str = ""


def _tokenize(text: str) -> set[str]:
    """Convert text into useful lowercase search tokens."""
    stop_words = {
        "a", "an", "the", "is", "are", "can", "i", "my", "be", "to", "of",
        "in", "for", "do", "does", "and", "or", "it", "this", "that", "with",
        "what", "when", "how", "should", "if", "was", "were", "from",
    }

    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return {token for token in tokens if len(token) > 2 and token not in stop_words}


def _load_policy_files(query_lower: str) -> dict[str, str]:
    """Load hinted policy files, or all policies when no hint matches."""
    target_files: set[str] = set()

    for keyword, files in KEYWORD_FILE_HINTS.items():
        if keyword in query_lower:
            target_files.update(files)

    if not target_files:
        target_files = {path.name for path in POLICIES_DIR.glob("*.txt")}

    loaded_files = {}

    for filename in sorted(target_files):
        path = POLICIES_DIR / filename
        if path.exists():
            loaded_files[filename] = path.read_text(encoding="utf-8")

    return loaded_files


def _chunk_text(text: str) -> list[str]:
    """Split policy text into overlapping line chunks."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks = []

    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)

    for start in range(0, len(lines), step):
        chunk_lines = lines[start:start + CHUNK_SIZE]
        if chunk_lines:
            chunks.append("\n".join(chunk_lines))

    return chunks


def _score_chunk(chunk: str, query_tokens: set[str]) -> int:
    """Score a chunk using keyword overlap plus a small phrase bonus."""
    chunk_lower = chunk.lower()
    chunk_tokens = _tokenize(chunk_lower)

    score = len(query_tokens & chunk_tokens)

    for token in query_tokens:
        if token in chunk_lower:
            score += 1

    return score


def run(user_query: str) -> RetrieverResult:
    """Retrieve the top policy chunks for the user query."""
    try:
        query = user_query.strip()
        query_lower = query.lower()
        query_tokens = _tokenize(query)

        policy_files = _load_policy_files(query_lower)

        if not policy_files:
            return RetrieverResult(error="No policy files were found in the policies directory.")

        scored_chunks: list[PolicyChunk] = []

        for filename, content in policy_files.items():
            for chunk in _chunk_text(content):
                score = _score_chunk(chunk, query_tokens)

                if score >= MIN_SCORE:
                    scored_chunks.append(
                        PolicyChunk(
                            source_file=filename,
                            content=chunk,
                            score=score,
                        )
                    )

        if not scored_chunks:
            return RetrieverResult(
                files_searched=list(policy_files.keys()),
                error=(
                    "No relevant policy sections were found. "
                    "Try asking with more specific terms such as refund, PII, escalation, fraud, or compliance."
                ),
            )

        scored_chunks.sort(key=lambda item: item.score, reverse=True)

        return RetrieverResult(
            chunks=scored_chunks[:TOP_K],
            files_searched=list(policy_files.keys()),
        )

    except Exception as exc:
        return RetrieverResult(error=f"Retriever agent failed: {exc}")