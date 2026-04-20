# rag/embedder.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Convert text chunks into vector embeddings and
# persist them in a local ChromaDB vector database.
#
# Why embeddings?
#   Embeddings turn text into numbers (vectors). Similar sentences
#   end up close together in vector space, so we can search by
#   meaning rather than exact keywords.
#
# Why HuggingFace instead of OpenAI?
#   The "all-MiniLM-L6-v2" model runs 100% locally — no API key,
#   no cost, no internet required after the first download.
#
# Used by: rag/pipeline.py → load_and_index_pdf()
# ─────────────────────────────────────────────────────────────

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Default storage location for the ChromaDB files on disk.
CHROMA_DIR = "./chroma_db"
COLLECTION  = "eduagent_docs"


def embed_and_store_chunks(chunks: list) -> None:
    """
    Embed a list of Document chunks and store them in ChromaDB.

    Args:
        chunks: List of LangChain Document objects from loader.py.
    """
    # Load the local sentence-transformer model.
    # On first run this downloads ~90 MB; subsequent runs use cache.
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Chroma.from_documents() embeds every chunk and saves the
    # vectors + raw text to the persist_directory on disk.
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION,
    )
