"""
agents/retriever_agent.py

Retrieves relevant sections from local policy text files.

Approach: simple keyword-overlap scoring over sentence-level chunks.
This is intentionally lightweight — no vector DB required — while still
being explainable and effective for a bounded document set.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
POLICIES_DIR = Path(__file__).parent.parent / "policies"
CHUNK_SIZE = 6          # Lines per chunk
CHUNK_OVERLAP = 2       # Overlap between adjacent chunks (sliding window)
TOP_K = 4               # Maximum number of chunks to return
MIN_SCORE = 1           # Minimum keyword matches to include a chunk

# Map common query terms to the most relevant policy file(s)
KEYWORD_FILE_HINTS: dict[str, list[str]] = {
    "refund":       ["refund_policy.txt"],
    "credit":       ["refund_policy.txt"],
    "reimburse":    ["refund_policy.txt"],
    "payment":      ["refund_policy.txt"],
    "money":        ["refund_policy.txt"],
    "pii":          ["pii_policy.txt"],
    "personal":     ["pii_policy.txt"],
    "ssn":          ["pii_policy.txt"],
    "social security": ["pii_policy.txt"],
    "data":         ["pii_policy.txt", "escalation_policy.txt"],
    "privacy":      ["pii_policy.txt"],
    "sensitive":    ["pii_policy.txt"],
    "escalat":      ["escalation_policy.txt"],
    "compliance":   ["escalation_policy.txt"],
    "legal":        ["escalation_policy.txt"],
    "fraud":        ["escalation_policy.txt", "refund_policy.txt"],
    "breach":       ["pii_policy.txt", "escalation_policy.txt"],
    "ticket":       ["escalation_policy.txt", "pii_policy.txt"],
    "gdpr":         ["pii_policy.txt", "escalation_policy.txt"],
    "ccpa":         ["pii_policy.txt", "escalation_policy.txt"],
}


@dataclass
class PolicyChunk:
    source_file: str
    content: str
    score: int      # Number of matching keywords — higher = more relevant


@dataclass
class RetrieverResult:
    chunks: list[PolicyChunk] = field(default_factory=list)
    files_searched: list[str] = field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_policy_files(query_lower: str) -> dict[str, str]:
    """
    Decide which policy files to search based on keyword hints,
    falling back to all files if no hint matches.
    """
    target_files: set[str] = set()
    for keyword, files in KEYWORD_FILE_HINTS.items():
        if keyword in query_lower:
            target_files.update(files)

    if not target_files:
        # No specific hint — search everything
        target_files = {f.name for f in POLICIES_DIR.glob("*.txt")}

    loaded: dict[str, str] = {}
    for filename in target_files:
        filepath = POLICIES_DIR / filename
        if filepath.exists():
            loaded[filename] = filepath.read_text(encoding="utf-8")

    return loaded


def _chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping line-based chunks.
    Keeps context intact better than hard character splits.
    """
    lines = [l for l in text.splitlines() if l.strip()]
    chunks = []
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    for i in range(0, len(lines), step):
        chunk_lines = lines[i: i + CHUNK_SIZE]
        if chunk_lines:
            chunks.append("\n".join(chunk_lines))
    return chunks


def _score_chunk(chunk: str, query_tokens: set[str]) -> int:
    """
    Count how many unique query tokens appear in the chunk.
    Case-insensitive, punctuation-stripped.
    """
    chunk_lower = re.sub(r"[^\w\s]", " ", chunk.lower())
    chunk_tokens = set(chunk_lower.split())
    return len(query_tokens & chunk_tokens)


def _tokenize_query(query: str) -> set[str]:
    """Extract meaningful tokens from the query (skip very short words)."""
    STOP_WORDS = {"a", "an", "the", "is", "are", "can", "i", "my", "be",
                  "to", "of", "in", "for", "do", "does", "and", "or", "it",
                  "this", "that", "with", "what", "when", "how", "should"}
    tokens = re.sub(r"[^\w\s]", " ", query.lower()).split()
    return {t for t in tokens if len(t) > 2 and t not in STOP_WORDS}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run(user_query: str) -> RetrieverResult:
    """
    Search local policy files and return the most relevant text chunks.

    Each chunk includes its source filename and a relevance score so the
    Analyst agent knows exactly where the information came from.
    """
    try:
        query_lower = user_query.lower()
        query_tokens = _tokenize_query(user_query)

        policy_files = _load_policy_files(query_lower)
        if not policy_files:
            return RetrieverResult(
                error="No policy files found in the policies/ directory."
            )

        all_chunks: list[PolicyChunk] = []

        for filename, content in policy_files.items():
            for chunk_text in _chunk_text(content):
                score = _score_chunk(chunk_text, query_tokens)
                if score >= MIN_SCORE:
                    all_chunks.append(PolicyChunk(
                        source_file=filename,
                        content=chunk_text,
                        score=score,
                    ))

        if not all_chunks:
            return RetrieverResult(
                files_searched=list(policy_files.keys()),
                error=(
                    "No sufficiently relevant policy sections found for this query. "
                    "Try rephrasing with more specific policy terms."
                ),
            )

        # Sort by score descending; take top-K
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        top_chunks = all_chunks[:TOP_K]

        return RetrieverResult(
            chunks=top_chunks,
            files_searched=list(policy_files.keys()),
        )

    except Exception as exc:
        return RetrieverResult(error=f"Retriever agent failed: {str(exc)}")
