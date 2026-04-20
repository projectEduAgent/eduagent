# rag/loader.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Load a PDF file from disk and split it into
# smaller text chunks that can be embedded and stored in ChromaDB.
#
# Why chunking?
#   LLMs have a limited context window. Splitting a large PDF into
#   small overlapping chunks lets us retrieve only the relevant
#   pieces instead of feeding the entire document to the model.
#
# Used by: rag/pipeline.py → load_and_index_pdf()
# ─────────────────────────────────────────────────────────────

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split_pdf(pdf_path: str) -> list:
    """
    Load a PDF and split it into overlapping text chunks.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A list of LangChain Document objects (chunks).
    """
    # PyPDFLoader reads every page of the PDF and returns a list of
    # Document objects, one per page.
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # RecursiveCharacterTextSplitter breaks each page into chunks.
    # chunk_size=500  → each chunk is at most 500 characters
    # chunk_overlap=50 → consecutive chunks share 50 characters so
    #                    context is not lost at boundaries
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(pages)
    return chunks
