# agents/answer_agent.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Generate a document-grounded answer to a student's
# question using a locally running Ollama LLM.
#
# How it works:
#   1. Receive the top-k chunks retrieved by the RAG pipeline.
#   2. Build a prompt that includes the chunks as "context".
#   3. Call the local Ollama model and return its response.
#
# The LLM never sees the full document — only the relevant chunks.
# This keeps answers focused and reduces hallucination.
#
# Depends on: Ollama running locally with qwen3.5:9b pulled.
#   → Start Ollama:   ollama serve
#   → Pull model:     ollama pull qwen3.5:9b
# ─────────────────────────────────────────────────────────────

import os

from langchain_ollama import OllamaLLM

# In Docker, OLLAMA_HOST is set to "http://ollama:11434" via docker-compose.
# When running locally without Docker it defaults to localhost.
_ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

llm = OllamaLLM(model="qwen3.5:9b", base_url=_ollama_host)


def generate_answer(question: str, chunks: list[dict]) -> str:
    """
    Generate an answer grounded in the retrieved document chunks.

    Args:
        question: The student's question.
        chunks:   List of chunk dicts with keys: text, source_file, page, chunk_index.

    Returns:
        A plain-text answer string from the LLM.
    """
    context = "\n\n".join(chunk["text"] for chunk in chunks)

    prompt = f"""You are a helpful academic assistant.
Answer the student's question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context}

Question: {question}

Answer:"""

    return llm.invoke(prompt)
