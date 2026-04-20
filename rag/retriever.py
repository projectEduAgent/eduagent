# rag/retriever.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Given a user question, find and return the most
# relevant text chunks from ChromaDB using vector similarity search.
#
# How it works:
#   1. The question is embedded into a vector using the same model
#      that was used during indexing.
#   2. ChromaDB compares that vector against all stored chunk vectors
#      using cosine similarity.
#   3. The top-k closest chunks are returned as plain strings.
#
# Used by: rag/pipeline.py → search()
# ─────────────────────────────────────────────────────────────

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Must match the values used in embedder.py
CHROMA_DIR = "./chroma_db"
COLLECTION  = "eduagent_docs"


def retrieve_top_chunks(question: str, k: int = 3) -> list[str]:
    """
    Return the top-k most relevant text chunks for a question.

    Args:
        question: The student's question as a plain string.
        k:        Number of chunks to return (default: 3).

    Returns:
        A list of plain text strings (the chunk contents).
    """
    # Use the same embedding model so question vectors and chunk
    # vectors live in the same vector space.
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Open the existing ChromaDB collection (must be indexed first).
    db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )

    # similarity_search returns Document objects; we extract .page_content
    results = db.similarity_search(question, k=k)
    return [doc.page_content for doc in results]
