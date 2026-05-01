# tests/test_evaluator.py
# ─────────────────────────────────────────────────────────────
# Unit tests for agents/evaluator_agent.py.
#
# All tests mock the LLM so they do NOT require Ollama running.
# ─────────────────────────────────────────────────────────────

import json
from unittest.mock import patch

import pytest

from agents.evaluator_agent import evaluate_answer, _parse_scores, _clamp_score


# ── _parse_scores() tests ──────────────────────────────────────

def test_parse_scores_valid_json():
    raw = '{"relevance": 8, "accuracy": 7, "completeness": 6, "feedback": "Good answer."}'
    result = _parse_scores(raw)
    assert result["relevance"] == 8.0
    assert result["accuracy"] == 7.0
    assert result["completeness"] == 6.0
    assert result["feedback"] == "Good answer."


def test_parse_scores_with_code_block():
    raw = '```json\n{"relevance": 9, "accuracy": 8, "completeness": 7, "feedback": "ok"}\n```'
    result = _parse_scores(raw)
    assert result["relevance"] == 9.0
    assert result["accuracy"] == 8.0
    assert result["completeness"] == 7.0


def test_parse_scores_malformed():
    result = _parse_scores("not json at all")
    assert result["relevance"] == 0.0
    assert result["accuracy"] == 0.0
    assert result["completeness"] == 0.0
    assert result["feedback"] == "parse_error"


def test_parse_scores_empty_string():
    result = _parse_scores("")
    assert result["relevance"] == 0.0
    assert result["feedback"] == "parse_error"


def test_parse_scores_partial_json():
    raw = '{"relevance": 5}'
    result = _parse_scores(raw)
    assert result["relevance"] == 5.0
    assert result["accuracy"] == 0.0
    assert result["completeness"] == 0.0
    assert result["feedback"] == ""


def test_parse_scores_clamps_above_ten():
    raw = '{"relevance": 15, "accuracy": 10, "completeness": 8, "feedback": "ok"}'
    result = _parse_scores(raw)
    assert result["relevance"] == 10.0
    assert result["accuracy"] == 10.0
    assert result["completeness"] == 8.0


def test_parse_scores_clamps_below_zero():
    raw = '{"relevance": -5, "accuracy": 3, "completeness": 0, "feedback": "ok"}'
    result = _parse_scores(raw)
    assert result["relevance"] == 0.0
    assert result["accuracy"] == 3.0
    assert result["completeness"] == 0.0


def test_clamp_score_nan():
    assert _clamp_score(float("nan")) == 0.0


def test_clamp_score_inf():
    assert _clamp_score(float("inf")) == 10.0
    assert _clamp_score(float("-inf")) == 0.0


def test_clamp_score_non_numeric():
    assert _clamp_score("abc") == 0.0
    assert _clamp_score(None) == 0.0


# ── evaluate_answer() tests ────────────────────────────────────

def test_evaluate_answer_returns_score():
    mock_response = json.dumps({
        "relevance": 8, "accuracy": 9, "completeness": 7, "feedback": "Well done."
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("What is ML?", "ML is AI.", [
            {"text": "ML is artificial intelligence."}
        ])
    assert "score" in result
    assert 0.0 <= result["score"] <= 10.0
    assert isinstance(result["score"], float)
    assert result["relevance"] == 8.0
    assert result["accuracy"] == 9.0
    assert result["completeness"] == 7.0
    assert result["feedback"] == "Well done."


def test_score_is_average():
    mock_response = json.dumps({
        "relevance": 9, "accuracy": 6, "completeness": 3, "feedback": "ok"
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("q", "a", [{"text": "c"}])
    expected = round((9 + 6 + 3) / 3, 2)
    assert result["score"] == expected


def test_evaluate_answer_empty_chunks():
    mock_response = json.dumps({
        "relevance": 5, "accuracy": 5, "completeness": 5, "feedback": "Average."
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("q", "a", [])
    assert "score" in result
    assert result["score"] == round((5 + 5 + 5) / 3, 2)


def test_evaluate_answer_uses_context():
    mock_response = json.dumps({
        "relevance": 10, "accuracy": 10, "completeness": 10, "feedback": "Perfect."
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        evaluate_answer("test?", "test answer", [
            {"text": "chunk one", "source_file": "a.pdf", "page": 1, "chunk_index": 0},
            {"text": "chunk two", "source_file": "a.pdf", "page": 2, "chunk_index": 1},
        ])
        call_args = mock_llm.invoke.call_args[0][0]
        assert "chunk one" in call_args
        assert "chunk two" in call_args


def test_evaluate_answer_result_structure():
    mock_response = json.dumps({
        "relevance": 7, "accuracy": 7, "completeness": 7, "feedback": "ok"
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("q", "a", [{"text": "c"}])
    required_keys = {"score", "relevance", "accuracy", "completeness", "feedback"}
    assert required_keys.issubset(result.keys())


def test_evaluate_answer_fallback_on_malformed_llm_output():
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = "I think this is a great answer!"
        result = evaluate_answer("q", "a", [{"text": "c"}])
    assert result["score"] == 0.0
    assert result["feedback"] == "parse_error"
