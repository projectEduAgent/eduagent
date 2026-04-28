import logging
import re


logger = logging.getLogger("monitor_agent")

UNSAFE_PATTERNS = [
    r"\b(harm|kill|weapon|illegal|drug|hack)\b",
    r"<script",
    r"ignore previous instructions",
]

REFUSAL_PHRASES = [
    "i don't have enough information",
    "i do not have enough information",
    "yeterli bilgiye sahip değilim",
    "cannot answer",
    "unable to answer",
]

MIN_WORD_LENGTH = 5
MIN_SOURCE_OVERLAP = 0.25


def _normalize_chunks(chunks: list) -> list[str]:
    """
    Normalize retrieved chunks into a list of plain text strings.

    Supports both the architecture doc contract (list[str]) and the
    current repository implementation (list[dict] with a "text" field).
    """
    normalized = []

    for chunk in chunks or []:
        if isinstance(chunk, str):
            normalized.append(chunk)
        elif isinstance(chunk, dict):
            text = chunk.get("text", "")
            if isinstance(text, str) and text.strip():
                normalized.append(text)

    return normalized


def _check_safety(answer: str) -> list[str]:
    """Return safety-related flags found in the answer."""
    flags = []
    text = answer.lower()

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(f"unsafe_pattern:{pattern}")

    return flags


def _check_grounding(answer: str, chunks: list) -> list[str]:
    """
    Check whether the answer appears grounded in the retrieved context.

    Uses a lightweight token-overlap heuristic on words with length >= 5.
    """
    normalized_chunks = _normalize_chunks(chunks)
    if not normalized_chunks:
        return ["no_context_available"]

    answer_words = set(re.findall(rf"\b\w{{{MIN_WORD_LENGTH},}}\b", answer.lower()))
    if not answer_words:
        return []

    combined_context = " ".join(normalized_chunks).lower()
    context_words = set(
        re.findall(rf"\b\w{{{MIN_WORD_LENGTH},}}\b", combined_context)
    )

    overlap = len(answer_words & context_words) / len(answer_words)
    if overlap < MIN_SOURCE_OVERLAP:
        return ["low_source_overlap"]

    return []


def _check_refusal(answer: str) -> list[str]:
    """Flag common refusal phrases that indicate the model did not answer."""
    text = answer.lower()

    for phrase in REFUSAL_PHRASES:
        if phrase in text:
            return ["llm_refused"]

    return []


def check_answer(answer: str, chunks: list, question: str) -> dict:
    """
    Run monitor checks and return the contract expected by the orchestrator.
    """
    flags = []
    flags.extend(_check_safety(answer))
    flags.extend(_check_grounding(answer, chunks))
    flags.extend(_check_refusal(answer))

    safety_flags = [flag for flag in flags if flag.startswith("unsafe_pattern:")]
    passed = len(safety_flags) == 0

    result = {
        "passed": passed,
        "flags": flags,
        "answer": answer,
    }

    if result["flags"]:
        logger.warning("Monitor flags: %s | Q: %s", result["flags"], question[:80])

    return result
