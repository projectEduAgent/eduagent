# app.py
# ─────────────────────────────────────────────────────────────
# EduAgent — Streamlit web interface.
#
# Flow:
#   1. Student uploads a PDF and clicks "Process PDF"
#      → PDF is chunked, embedded, and stored in ChromaDB
#   2. Student types a question and clicks "Search"
#      → Top 3 relevant chunks are retrieved from ChromaDB
#      → Chunks + question are sent to the Ollama LLM
#      → Answer is displayed on screen
#
# Run with:  streamlit run app.py
# ─────────────────────────────────────────────────────────────

import tempfile

import streamlit as st

from agents.answer_agent import generate_answer
from agents.retrieval_agent import retrieve
from rag.pipeline import load_and_index_pdf

# ── Page config ───────────────────────────────────────────────
st.set_page_config(page_title="EduAgent", page_icon="📚")
st.title("EduAgent — Academic Assistant")
st.write("Upload a PDF, index it, then ask any question about it.")

# ── Step 1: PDF Upload & Indexing ────────────────────────────
st.header("Step 1: Upload a PDF")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Streamlit gives us a file-like object; PyPDFLoader needs a real
    # file path, so we save it to a temporary file first.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    if st.button("Process PDF"):
        with st.spinner("Reading and indexing PDF — this may take a moment..."):
            load_and_index_pdf(tmp_path)   # chunk → embed → store
        st.success("PDF indexed successfully. You can now ask questions.")

# ── Step 2: Question & Answer ─────────────────────────────────
st.header("Step 2: Ask a Question")

question = st.text_input("Your question")

if st.button("Search"):
    if not question.strip():
        st.warning("Please enter a question before searching.")
    else:
        # Retrieve the top 3 chunks most relevant to the question.
        with st.spinner("Searching the document..."):
            chunks = retrieve(question)

        if not chunks:
            st.info("No results found. Make sure you have processed a PDF first.")
        else:
            # Send chunks + question to the local LLM for a grounded answer.
            with st.spinner("Generating answer with Ollama (qwen3.5:9b)..."):
                answer = generate_answer(question, chunks)

            st.subheader("Answer")
            st.write(answer)

            # Let the student inspect the source material used.
            with st.expander("Show retrieved source chunks"):
                for i, chunk in enumerate(chunks, start=1):
                    st.markdown(f"**Chunk {i}** — {chunk['source_file']}, page {chunk['page']}")
                    st.write(chunk["text"])
