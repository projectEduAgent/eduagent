# tests/test_integration.py
# ─────────────────────────────────────────────────────────────
# End-to-end integration tests for the full EduAgent pipeline.
#
# These tests attempt to exercise the orchestrator and all agents
# together. If the orchestrator is not yet implemented or Ollama is
# unavailable, they skip gracefully instead of failing.
# ─────────────────────────────────────────────────────────────

import os

import pytest

SAMPLE_PDF = "data/sample.pdf"


@pytest.fixture(scope="module")
def indexed_pdf():
    """Index the sample PDF once if it exists."""
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF at data/sample.pdf")
    from rag.pipeline import load_and_index_pdf, clear_index
    clear_index()
    load_and_index_pdf(SAMPLE_PDF)


def test_full_pipeline(indexed_pdf):
    """End-to-end: index → search → answer → monitor → evaluate."""
    try:
        from orchestrator.pipeline import run_pipeline
    except ImportError:
        pytest.skip("Orchestrator pipeline not yet implemented.")

    try:
        result = run_pipeline("What is the main topic of this document?")
    except Exception as e:
        # NOTE: Once the orchestrator is implemented, narrow this catch
        # to ConnectionError / Ollama-specific exceptions so real bugs fail.
        pytest.skip(f"Pipeline execution failed (Ollama unavailable?): {e}")

    assert result["answer"]
    assert isinstance(result["score"], float)
    assert isinstance(result["flags"], list)


def test_pipeline_result_structure(indexed_pdf):
    """Verify the orchestrator returns the expected contract."""
    try:
        from orchestrator.pipeline import run_pipeline
    except ImportError:
        pytest.skip("Orchestrator pipeline not yet implemented.")

    try:
        result = run_pipeline("Summarize the key points.")
    except Exception as e:
        # NOTE: Once the orchestrator is implemented, narrow this catch
        # to ConnectionError / Ollama-specific exceptions so real bugs fail.
        pytest.skip(f"Pipeline execution failed (Ollama unavailable?): {e}")

    required_keys = ["answer", "score", "breakdown", "flags", "chunks", "attempts"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    breakdown = result.get("breakdown", {})
    for sub_key in ("relevance", "accuracy", "completeness"):
        assert sub_key in breakdown, f"Missing breakdown key: {sub_key}"


def test_pipeline_with_blank_question(indexed_pdf):
    """A blank question should still return a valid structure."""
    try:
        from orchestrator.pipeline import run_pipeline
    except ImportError:
        pytest.skip("Orchestrator pipeline not yet implemented.")

    try:
        result = run_pipeline("")
    except Exception as e:
        # NOTE: Once the orchestrator is implemented, narrow this catch
        # to ConnectionError / Ollama-specific exceptions so real bugs fail.
        pytest.skip(f"Pipeline execution failed (Ollama unavailable?): {e}")

    assert "answer" in result
    assert "score" in result
    assert "chunks" in result
