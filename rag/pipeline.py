# rag/pipeline.py
# ─────────────────────────────────────────────────────────────
# This is the SINGLE ENTRY POINT for the entire RAG pipeline.
#
# Other agents (Monitor, Evaluator, Answer Agent, etc.) should
# ONLY import from this file — not from loader, embedder, or
# retriever directly. This keeps the internals easy to change
# without breaking other agents.
#
# Quick-start for teammates:
#
#   from rag.pipeline import load_and_index_pdf, search
#
#   # Step 1 — index a PDF (once per document upload)
#   load_and_index_pdf("path/to/document.pdf")
#
#   # Step 2 — retrieve relevant chunks for any question
#   chunks = search("What is Q-Learning?")
#   # chunks → ["Q-Learning is ...", "The reward function ...", ...]
#
# ─────────────────────────────────────────────────────────────

from rag.loader import load_and_split_pdf
from rag.embedder import embed_and_store_chunks
from rag.retriever import retrieve_top_chunks


def load_and_index_pdf(pdf_path: str) -> None:
    """
    Full ingestion pipeline: load a PDF, chunk it, embed it,
    and persist the vectors in ChromaDB.

    Call this once every time a new document is uploaded.

    Args:
        pdf_path: Path to the PDF file to index.
    """
    chunks = load_and_split_pdf(pdf_path)   # Step 1: read & split
    embed_and_store_chunks(chunks)           # Step 2: embed & store


def search(question: str, k: int = 3) -> list[str]:
    """
    Retrieve the most relevant chunks for a student's question.

    Call this every time you need context before generating an answer.

    Args:
        question: The student's question as a plain string.
        k:        How many chunks to return (default: 3).

    Returns:
        A list of text strings, ordered by relevance.
    """
    return retrieve_top_chunks(question, k=k)
