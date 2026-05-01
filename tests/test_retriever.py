# tests/test_retriever.py
# ─────────────────────────────────────────────────────────────
# Unit tests for rag/retriever.py.
#
# Mocked to avoid loading the embedding model during tests.
# ─────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch

import pytest

from rag.retriever import retrieve_top_chunks


def _make_doc(page_content: str, metadata: dict = None):
    """Build a minimal Document-like result from Chroma."""
    doc = MagicMock()
    doc.page_content = page_content
    doc.metadata = metadata or {}
    return doc


@patch("rag.retriever.Chroma")
@patch("rag.retriever._get_embeddings")
def test_retrieve_top_chunks_returns_list_of_dicts(mock_get_emb, mock_chroma_cls):
    """retrieve_top_chunks should return list[dict]."""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = [
        _make_doc("chunk one", {"source_file": "a.pdf", "page": 1, "chunk_index": 0}),
        _make_doc("chunk two", {"source_file": "a.pdf", "page": 2, "chunk_index": 1}),
    ]
    mock_chroma_cls.return_value = mock_db

    results = retrieve_top_chunks("question", k=2)

    assert isinstance(results, list)
    assert len(results) == 2
    for r in results:
        assert isinstance(r, dict)


@patch("rag.retriever.Chroma")
@patch("rag.retriever._get_embeddings")
def test_retrieve_top_chunks_has_required_keys(mock_get_emb, mock_chroma_cls):
    """Each dict must have text, source_file, page, chunk_index."""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = [
        _make_doc("text", {"source_file": "f.pdf", "page": 3, "chunk_index": 5}),
    ]
    mock_chroma_cls.return_value = mock_db

    results = retrieve_top_chunks("q", k=1)
    r = results[0]
    assert r["text"] == "text"
    assert r["source_file"] == "f.pdf"
    assert r["page"] == 3
    assert r["chunk_index"] == 5


@patch("rag.retriever.Chroma")
@patch("rag.retriever._get_embeddings")
def test_retrieve_top_chunks_defaults_for_missing_metadata(mock_get_emb, mock_chroma_cls):
    """Missing metadata should default to sensible values."""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = [
        _make_doc("text", {}),
    ]
    mock_chroma_cls.return_value = mock_db

    results = retrieve_top_chunks("q", k=1)
    r = results[0]
    assert r["source_file"] == "unknown"
    assert r["page"] == 0
    assert r["chunk_index"] == 0


@patch("rag.retriever.Chroma")
@patch("rag.retriever._get_embeddings")
def test_retrieve_top_chunks_passes_k(mock_get_emb, mock_chroma_cls):
    """The k parameter should be forwarded to similarity_search."""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = []
    mock_chroma_cls.return_value = mock_db

    retrieve_top_chunks("q", k=5)

    mock_db.similarity_search.assert_called_once_with("q", k=5)


@patch("rag.retriever.Chroma")
@patch("rag.retriever._get_embeddings")
def test_retrieve_top_chunks_empty_result(mock_get_emb, mock_chroma_cls):
    """An empty DB result should return an empty list."""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = []
    mock_chroma_cls.return_value = mock_db

    results = retrieve_top_chunks("q", k=3)
    assert results == []
