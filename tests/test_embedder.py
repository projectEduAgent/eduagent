# tests/test_embedder.py
# ─────────────────────────────────────────────────────────────
# Unit tests for rag/embedder.py.
#
# These tests mock ChromaDB and HuggingFaceEmbeddings to avoid
# loading the 90MB model during unit tests.
# ─────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch

import pytest

from rag.embedder import embed_and_store_chunks, clear_collection


def _make_chunk(text: str, metadata: dict = None):
    """Helper to build a minimal Document-like chunk."""
    chunk = MagicMock()
    chunk.page_content = text
    chunk.metadata = metadata or {}
    return chunk


@patch("rag.embedder.Chroma")
@patch("rag.embedder._get_embeddings")
def test_embed_and_store_chunks_tags_metadata(mock_get_emb, mock_chroma_cls):
    """embed_and_store_chunks should add source_file and chunk_index."""
    mock_chroma_cls.from_documents.return_value = None
    chunks = [_make_chunk("hello"), _make_chunk("world")]

    embed_and_store_chunks(chunks, source_filename="lecture.pdf")

    assert chunks[0].metadata["source_file"] == "lecture.pdf"
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[1].metadata["source_file"] == "lecture.pdf"
    assert chunks[1].metadata["chunk_index"] == 1


@patch("rag.embedder.Chroma")
@patch("rag.embedder._get_embeddings")
def test_embed_and_store_chunks_calls_chroma(mock_get_emb, mock_chroma_cls):
    """embed_and_store_chunks should call Chroma.from_documents."""
    mock_chroma_cls.from_documents.return_value = None
    chunks = [_make_chunk("test")]

    embed_and_store_chunks(chunks, source_filename="doc.pdf")

    mock_chroma_cls.from_documents.assert_called_once()
    call_kwargs = mock_chroma_cls.from_documents.call_args.kwargs
    assert call_kwargs["documents"] == chunks
    assert call_kwargs["collection_name"] == "eduagent_docs"


@patch("rag.embedder.Chroma")
@patch("rag.embedder._get_embeddings")
def test_clear_collection_deletes(mock_get_emb, mock_chroma_cls):
    """clear_collection should instantiate Chroma and call delete_collection."""
    mock_db = MagicMock()
    mock_chroma_cls.return_value = mock_db

    clear_collection()

    mock_chroma_cls.assert_called_once()
    mock_db.delete_collection.assert_called_once()


@patch("rag.embedder.Chroma")
@patch("rag.embedder._get_embeddings")
def test_clear_collection_graceful_on_error(mock_get_emb, mock_chroma_cls):
    """clear_collection should not raise if delete_collection fails."""
    mock_db = MagicMock()
    mock_db.delete_collection.side_effect = RuntimeError("boom")
    mock_chroma_cls.return_value = mock_db

    clear_collection()  # should not raise
