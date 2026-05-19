"""
Retriever agent.

Searches local policy files and returns the most relevant policy chunks.
Uses intent mapping and synonym expansion for more robust retrieval.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


POLICIES_DIR = Path(__file__).parent.parent / "policies"

CHUNK_SIZE = 6
CHUNK_OVERLAP = 2
TOP_K = 5
MIN_SCORE = 1


# ---------------------------------------------------------------------------
# Intent → policy file mapping
# Covers paraphrased and natural-language queries without exact keyword matches.
# ---------------------------------------------------------------------------

INTENT_GROUPS: dict[str, list[str]] = {
    "refund_policy.txt": [
        "refund", "credit", "reimburse", "reimbursement", "payment", "money",
        "charge", "overcharge", "billed", "billing", "invoice", "overpaid",
        "pay back", "return payment", "dispute", "wrong amount", "incorrect charge",
        "transaction", "cashback",
    ],
    "pii_policy.txt": [
        "pii", "personal", "ssn", "social security", "privacy", "sensitive",
        "customer data", "data protection", "gdpr", "ccpa", "hipaa",
        "email address", "phone number", "home address", "date of birth",
        "identification", "passport", "driver license", "biometric",
        "medical record", "health information", "confidential data",
        "data handling", "data sharing", "personally identifiable",
    ],
    "escalation_policy.txt": [
        "escalat", "compliance", "legal", "fraud", "breach", "ticket",
        "supervisor", "manager approval", "tier 2", "tier 1", "team lead",
        "cannot resolve", "unresolved", "complaint", "chargeback",
        "regulatory", "subpoena", "audit", "violation", "vip account",
        "refer to", "elevate",
    ],
    "hr_pto_policy.txt": [
        "pto", "vacation", "time off", "leave", "sick", "sick day", "sick leave",
        "holiday", "absence", "day off", "days off", "take off", "out of office",
        "parental leave", "maternity", "paternity", "bereavement", "fmla",
        "accrual", "accrued", "carry over", "carryover", "annual leave",
        "personal day", "paid leave", "unpaid leave", "next week",
        "schedule off", "approve my leave", "time away", "out next",
    ],
    "expense_travel_policy.txt": [
        "expense", "expenses", "reimburs", "receipt", "receipts",
        "client dinner", "business meal", "team lunch", "lunch", "dinner",
        "travel", "flight", "hotel", "accommodation", "car rental",
        "mileage", "per diem", "uber", "lyft", "taxi", "rideshare",
        "airfare", "booking", "conference travel", "client entertainment",
        "business trip", "away on business", "offsite", "spend", "pay for",
        "submit an expense", "expense report", "out of pocket",
    ],
    "remote_work_equipment_policy.txt": [
        "remote", "work from home", "wfh", "hybrid", "home office",
        "equipment", "laptop", "monitor", "keyboard", "headset", "peripherals",
        "company device", "personal device", "byod", "mdm",
        "vpn", "acceptable use", "software install", "it request",
        "new monitor", "second screen", "standing desk", "docking station",
        "internet at home", "home setup", "equipment request",
        "return laptop", "return equipment", "lost laptop", "stolen device",
    ],
}


# ---------------------------------------------------------------------------
# Light synonym expansion for scoring boosts
# Improves recall on paraphrased queries without false positives.
# ---------------------------------------------------------------------------

SYNONYM_MAP: dict[str, list[str]] = {
    "pto": ["vacation", "time off", "leave", "annual leave"],
    "reimburse": ["refund", "repay", "pay back", "expense"],
    "reimbursement": ["refund", "expense", "repayment"],
    "leave": ["pto", "time off", "vacation", "absence"],
    "vacation": ["pto", "time off", "leave", "holiday"],
    "dinner": ["meal", "entertainment", "client meal", "restaurant"],
    "lunch": ["meal", "team lunch", "business meal"],
    "expense": ["reimburse", "receipt", "spend", "cost"],
    "wfh": ["remote", "work from home", "home office"],
    "laptop": ["equipment", "device", "computer", "asset"],
    "escalate": ["refer", "elevate", "supervisor", "manager"],
    "breach": ["incident", "violation", "data loss", "security event"],
    "fraud": ["abuse", "suspicious", "flagged", "trust and safety"],
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
    matched_intent: str = ""
    error: str = ""


def _tokenize(text: str) -> set[str]:
    """Convert text into useful lowercase search tokens."""
    stop_words = {
        "a", "an", "the", "is", "are", "can", "i", "my", "be", "to", "of",
        "in", "for", "do", "does", "and", "or", "it", "this", "that", "with",
        "what", "when", "how", "should", "if", "was", "were", "from", "get",
        "me", "us", "we", "they", "our", "have", "has", "had", "will", "would",
        "could", "need", "want", "about", "which", "who", "at", "on", "by",
    }
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return {t for t in tokens if len(t) > 2 and t not in stop_words}


def _expand_tokens(tokens: set[str]) -> set[str]:
    """Add synonym expansions to the token set for broader matching."""
    expanded = set(tokens)
    for token in list(tokens):
        if token in SYNONYM_MAP:
            expanded.update(SYNONYM_MAP[token])
    return expanded


def _detect_intent(query_lower: str) -> list[str]:
    """
    Identify which policy file(s) best match the user's query.
    Uses substring matching against the intent groups, which handles
    paraphrased questions better than exact keyword lookup alone.
    """
    file_scores: dict[str, int] = {}

    for filename, signals in INTENT_GROUPS.items():
        score = 0
        for signal in signals:
            if signal in query_lower:
                # Multi-word signals are weighted more heavily
                weight = 2 if " " in signal else 1
                score += weight
        if score > 0:
            file_scores[filename] = score

    if not file_scores:
        return []

    # Return all files above half the top score to allow cross-policy queries
    top_score = max(file_scores.values())
    threshold = max(1, top_score // 2)
    return [f for f, s in file_scores.items() if s >= threshold]


def _load_policy_files(query_lower: str) -> tuple[dict[str, str], str]:
    """Load the policy files most relevant to the query intent."""
    target_files = _detect_intent(query_lower)
    intent_label = ""

    if target_files:
        intent_label = ", ".join(
            f.replace("_", " ").replace(".txt", "") for f in target_files
        )
    else:
        # No intent detected — search all policies
        target_files = [p.name for p in POLICIES_DIR.glob("*.txt")]

    loaded: dict[str, str] = {}
    for filename in sorted(target_files):
        path = POLICIES_DIR / filename
        if path.exists():
            loaded[filename] = path.read_text(encoding="utf-8")

    return loaded, intent_label


def _chunk_text(text: str) -> list[str]:
    """Split policy text into overlapping line chunks."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks = []
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    for start in range(0, len(lines), step):
        chunk_lines = lines[start : start + CHUNK_SIZE]
        if chunk_lines:
            chunks.append("\n".join(chunk_lines))
    return chunks


def _score_chunk(chunk: str, query_tokens: set[str], expanded_tokens: set[str]) -> int:
    """
    Score a chunk on both exact query tokens and expanded synonyms.
    Exact matches score higher; synonym matches provide a softer signal.
    """
    chunk_lower = chunk.lower()
    chunk_tokens = _tokenize(chunk_lower)

    # Exact token overlap (primary signal)
    exact_score = len(query_tokens & chunk_tokens)

    # Substring match bonus for exact tokens (catches partial matches)
    for token in query_tokens:
        if len(token) > 3 and token in chunk_lower:
            exact_score += 1

    # Synonym expansion overlap (secondary signal, half weight)
    synonym_only = expanded_tokens - query_tokens
    synonym_score = len(synonym_only & chunk_tokens) // 2

    return exact_score + synonym_score


def run(user_query: str) -> RetrieverResult:
    """Retrieve the top policy chunks for the user query."""
    try:
        query = user_query.strip()
        query_lower = query.lower()
        query_tokens = _tokenize(query)
        expanded_tokens = _expand_tokens(query_tokens)

        policy_files, intent_label = _load_policy_files(query_lower)

        if not policy_files:
            return RetrieverResult(
                error="No policy files were found in the policies directory."
            )

        scored_chunks: list[PolicyChunk] = []

        for filename, content in policy_files.items():
            for chunk in _chunk_text(content):
                score = _score_chunk(chunk, query_tokens, expanded_tokens)
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
                matched_intent=intent_label,
                error=(
                    "No closely matching policy sections were found. "
                    "The question may be outside current policy coverage, or try rephrasing "
                    "with more specific terms."
                ),
            )

        scored_chunks.sort(key=lambda c: c.score, reverse=True)

        return RetrieverResult(
            chunks=scored_chunks[:TOP_K],
            files_searched=list(policy_files.keys()),
            matched_intent=intent_label,
        )

    except Exception as exc:
        return RetrieverResult(error=f"Retriever agent failed: {exc}")
