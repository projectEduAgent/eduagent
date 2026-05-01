# tests/test_loader.py
# ─────────────────────────────────────────────────────────────
# Unit tests for rag/loader.py.
# ─────────────────────────────────────────────────────────────

import os
from unittest.mock import MagicMock, patch

import pytest

from rag.loader import load_and_split_pdf

SAMPLE_PDF = "data/sample.pdf"


def test_load_and_split_pdf_returns_list():
    """load_and_split_pdf should return a list."""
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF at data/sample.pdf")
    chunks = load_and_split_pdf(SAMPLE_PDF)
    assert isinstance(chunks, list)


def test_load_and_split_pdf_chunks_have_page_content():
    """Each chunk should have page_content attribute."""
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF at data/sample.pdf")
    chunks = load_and_split_pdf(SAMPLE_PDF)
    assert len(chunks) > 0
    for chunk in chunks:
        assert hasattr(chunk, "page_content")
        assert isinstance(chunk.page_content, str)
        assert len(chunk.page_content) > 0


def test_load_and_split_pdf_chunks_have_metadata():
    """Each chunk should have metadata dict."""
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF at data/sample.pdf")
    chunks = load_and_split_pdf(SAMPLE_PDF)
    assert len(chunks) > 0
    for chunk in chunks:
        assert hasattr(chunk, "metadata")
        assert isinstance(chunk.metadata, dict)


@patch("rag.loader.PyPDFLoader")
def test_load_and_split_pdf_uses_pypdf_loader(mock_loader_cls):
    """The function should instantiate PyPDFLoader with the given path."""
    mock_loader = MagicMock()
    mock_loader.load.return_value = []
    mock_loader_cls.return_value = mock_loader

    load_and_split_pdf("fake/path.pdf")
    mock_loader_cls.assert_called_once_with("fake/path.pdf")
    mock_loader.load.assert_called_once()
