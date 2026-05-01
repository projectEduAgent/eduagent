from agents.monitor_agent import (
    _check_grounding,
    _check_safety,
    check_answer,
)


SAMPLE_CHUNKS = [
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by biological neurons.",
]

SAMPLE_DICT_CHUNKS = [
    {
        "text": "Machine learning is a subset of artificial intelligence.",
        "source_file": "sample.pdf",
        "page": 1,
        "chunk_index": 0,
    },
    {
        "text": "Neural networks are inspired by biological neurons.",
        "source_file": "sample.pdf",
        "page": 1,
        "chunk_index": 1,
    },
]


def test_check_safety_detects_unsafe_pattern():
    flags = _check_safety("You should hack the system to learn faster.")
    assert any(flag.startswith("unsafe_pattern:") for flag in flags)


def test_clean_answer_passes():
    answer = "Machine learning is a subset of artificial intelligence."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is ML?")
    assert result["passed"] is True
    assert result["answer"] == answer
    assert result["flags"] == []


def test_unsafe_content_fails():
    answer = "You should hack the system to learn faster."
    result = check_answer(answer, SAMPLE_CHUNKS, "How to learn?")
    assert result["passed"] is False
    assert any("unsafe_pattern:" in flag for flag in result["flags"])


def test_low_grounding_flagged():
    answer = "Quantum entanglement destroys parallel universes instantly."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is entanglement?")
    assert "low_source_overlap" in result["flags"]


def test_refusal_detected():
    answer = "I don't have enough information to answer that."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is X?")
    assert "llm_refused" in result["flags"]


def test_empty_chunks_flagged():
    result = check_answer("Some answer.", [], "Question?")
    assert "no_context_available" in result["flags"]


def test_result_structure():
    result = check_answer("test answer", SAMPLE_CHUNKS, "test?")
    assert "passed" in result
    assert "flags" in result
    assert "answer" in result
    assert isinstance(result["flags"], list)


def test_grounding_supports_dict_chunks():
    answer = "Machine learning is a subset of artificial intelligence."
    flags = _check_grounding(answer, SAMPLE_DICT_CHUNKS)
    assert flags == []


def test_check_answer_supports_dict_chunks():
    answer = "Neural networks are inspired by biological neurons."
    result = check_answer(answer, SAMPLE_DICT_CHUNKS, "What are neural networks?")
    assert result["passed"] is True
    assert result["flags"] == []
