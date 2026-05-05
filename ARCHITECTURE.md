# EduAgent — Full Architecture Plan
> April 2026 · 7-Person Team · LLM Homework Project

---

## 1. System Overview

EduAgent is a multi-agent academic assistant. Students upload PDF documents; the system chunks, embeds, and stores them in a local vector database. When a student asks a question, four agents work in sequence to produce a high-quality, grounded, verified answer.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Streamlit UI)                         │
│   Upload PDF  ──►  Process  ──►  Ask Question  ──►  Read Answer    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│               orchestrator/pipeline.py  (Member 1 - Murat)                  │
│  Ties all agents together. Calls them in sequence, passes outputs.  │
└──┬──────────────────────────────────────────────────────────────────┘
   │
   │  Step 1
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│           RAG Pipeline  (Kerem — Member 2) ✅ COMPLETE              │
│  rag/pipeline.py  →  load_and_index_pdf()  /  search()             │
│  Internally: loader → embedder → ChromaDB → retriever              │
└──┬──────────────────────────────────────────────────────────────────┘
   │ returns: List[str]  (top-k text chunks)
   │  Step 2
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Answer Agent  (Member 4-Ezgi)  ← extends Kerem's base       │
│  agents/answer_agent.py                                             │
│  Builds a rich prompt → calls Ollama LLM → returns answer string   │
└──┬──────────────────────────────────────────────────────────────────┘
   │ returns: str  (raw answer)
   │  Step 3
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Monitor Agent  (Member 5 — Aykut Akkuş)               │
│  agents/monitor_agent.py                                            │
│  Checks answer for hallucinations, safety, source grounding        │
└──┬──────────────────────────────────────────────────────────────────┘
   │ returns: MonitorResult  {passed: bool, flags: list, answer: str}
   │  Step 4
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Evaluator Agent  (Member 6 — Yağız Efe Gökçe)         │
│  agents/evaluator_agent.py                                          │
│  Scores answer on Relevance / Accuracy / Completeness (0-10)       │
│  Triggers retry loop if score < threshold (max 2 retries)          │
└──┬──────────────────────────────────────────────────────────────────┘
   │ returns: EvalResult  {score: float, breakdown: dict, answer: str}
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Streamlit UI  (Member 7 — Zeynep Uygur)  ← extends Kerem's skeleton  │
│  app.py                                                             │
│  Chat bubbles, score badge, source expander, session history       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Canonical File & Owner Map

```
eduagent/
├── agents/
│   ├── __init__.py
│   ├── retrieval_agent.py     ← Zeynep Çavuş (Member 3)  (create from scratch)
│   ├── answer_agent.py        ← Ezgi (Member 4)  (base exists, needs full build)
│   ├── monitor_agent.py       ← Aykut Akkuş ✅  (create from scratch)
│   └── evaluator_agent.py     ← Yağız Efe Gökçe (Member 6)  (create from scratch)
├── rag/
│   ├── __init__.py
│   ├── pipeline.py            ← Kerem ✅  (DO NOT MODIFY — public API)
│   ├── loader.py              ← Kerem ✅
│   ├── embedder.py            ← Kerem ✅
│   └── retriever.py           ← Kerem ✅
├── orchestrator/
│   └── pipeline.py            ← Member 1  (create from scratch)
├── ui/
│   └── app.py                 ← Zeynep Uygur (Member 7)  (replaces root app.py skeleton)
├── tests/
│   ├── test_retrieval.py      ← Zeynep Çavuş (Member 3)
│   ├── test_answer.py         ← Ezgi (Member 4)
│   ├── test_monitor.py        ← Aykut Akkuş ✅ 
│   ├── test_evaluator.py      ← Yağız Efe Gökçe (Member 6)
│   └── test_integration.py   ← Yağız Efe Gökçe (Member 6)
├── data/                      ← sample PDFs for testing (all members)
├── app.py                     ← Kerem's skeleton (Zeynep Uygur migrates to ui/)
├── Dockerfile                 ← Kerem ✅
├── docker-compose.yml         ← Kerem ✅
├── requirements.txt           ← Kerem ✅  (members add their deps here)
├── .env.example               ← Kerem ✅
└── README.md                  ← Member 1 expands to full project README
```

---

## 3. Shared Data Contracts

Every agent must agree on these exact signatures. **Do not change them without telling the team.**

```python
# What the RAG pipeline exposes (Kerem's public API — read-only)
from rag.pipeline import load_and_index_pdf, search

load_and_index_pdf(pdf_path: str) -> None
search(question: str, k: int = 3) -> list[str]

# What the orchestrator expects from each agent
from agents.retrieval_agent import retrieve
from agents.answer_agent    import generate_answer
from agents.monitor_agent   import check_answer
from agents.evaluator_agent import evaluate_answer

retrieve(question: str, k: int = 3) -> list[str]
# Thin wrapper around rag.pipeline.search() — the orchestrator always
# goes through the agent layer, never calls rag/ directly.

generate_answer(question: str, chunks: list[str]) -> str

check_answer(
    answer: str,
    chunks: list[str],   # same chunks used to generate the answer
    question: str
) -> dict:
    # {
    #   "passed": bool,
    #   "flags": list[str],   # e.g. ["hallucination_risk", "unsafe_content"]
    #   "answer": str         # possibly cleaned answer
    # }

evaluate_answer(
    question: str,
    answer: str,
    chunks: list[str]
) -> dict:
    # {
    #   "score": float,          # 0.0 – 10.0
    #   "relevance": float,
    #   "accuracy": float,
    #   "completeness": float,
    #   "feedback": str          # one-line explanation
    # }
```

---

## 4. Member-by-Member Instructions

---

### Member 1 — Project Manager & Orchestrator Developer - Murat ✅ COMPLETE

**Your job:** You own the glue. `orchestrator/pipeline.py` is the brain that calls all four agents in order and handles the retry loop when the evaluator score is low.

#### Files you own
- `orchestrator/pipeline.py`
- `README.md` (project-level, not Kerem's rag README)
- GitHub branch strategy + issue tracking

#### Step-by-step tasks

**Task 1 — Branch Strategy (Day 1)**

Set up GitHub with these branches:
```
main          ← production-ready only. Never push directly.
develop       ← integration branch. All feature branches merge here.
feature/orchestrator
feature/answer-agent
feature/monitor-agent
feature/evaluator-agent
feature/ui
```

Create a `CONTRIBUTING.md` with:
- "Always branch from `develop`"
- "PR requires 1 reviewer approval"
- "Run `pytest tests/` before opening a PR"

**Task 2 — Write `orchestrator/pipeline.py`**

```python
# orchestrator/pipeline.py
from agents.retrieval_agent import retrieve
from agents.answer_agent    import generate_answer
from agents.monitor_agent   import check_answer
from agents.evaluator_agent import evaluate_answer

SCORE_THRESHOLD = 6.0
MAX_RETRIES = 2

def run_pipeline(question: str) -> dict:
    """
    Full agent pipeline. Returns a dict with answer, score, flags, chunks.
    This is what the UI calls — it never imports agents directly.
    """
    chunks = retrieve(question, k=3)

    answer = generate_answer(question, chunks)

    for attempt in range(MAX_RETRIES + 1):
        monitor_result = check_answer(answer, chunks, question)
        if not monitor_result["passed"]:
            # Monitor flagged it — regenerate immediately, don't evaluate
            answer = generate_answer(question, chunks)
            continue

        eval_result = evaluate_answer(question, answer, chunks)

        if eval_result["score"] >= SCORE_THRESHOLD or attempt == MAX_RETRIES:
            return {
                "answer": answer,
                "score": eval_result["score"],
                "breakdown": {
                    "relevance": eval_result["relevance"],
                    "accuracy": eval_result["accuracy"],
                    "completeness": eval_result["completeness"],
                },
                "feedback": eval_result["feedback"],
                "flags": monitor_result["flags"],
                "chunks": chunks,
                "attempts": attempt + 1,
            }

        # Score too low — ask Answer Agent to try again
        answer = generate_answer(question, chunks)

    # Fallback (should not reach here)
    return {"answer": answer, "score": 0.0, "chunks": chunks, "attempts": MAX_RETRIES}
```

**Task 3 — Expand `README.md`**

The project-level README (not Kerem's `rag/README.md`) should cover:
- What EduAgent is (2 paragraphs)
- System architecture diagram (copy from this document)
- How to run with Docker (copy from Kerem's README and adapt)
- How to run locally
- Team member list

**Task 4 — Integration smoke test**

After all agents are merged into `develop`, write a script `scripts/smoke_test.py`:
```python
from rag.pipeline import load_and_index_pdf
from orchestrator.pipeline import run_pipeline

load_and_index_pdf("data/sample.pdf")
result = run_pipeline("What is the main topic of this document?")
print(result)
assert result["score"] > 0
assert result["answer"]
```

#### Checklist
- [x] GitHub repo with branch strategy
- [x] `orchestrator/pipeline.py` with retry loop
- [x] README.md complete
- [x] Smoke test script
- [ ] Sprint planning (use GitHub Projects, create 4 milestone columns)

---

### Member 2 — Kerem (RAG Pipeline) ✅ COMPLETE

**Your work is done. See Section 5 for the review and open questions.**

Your `rag/pipeline.py` is the public API. Only **two** things import from it:
```python
# 1. Zeynep Çavuş's retrieval_agent.py (the only agent that touches rag/)
from rag.pipeline import search

# 2. The Streamlit UI for document indexing (upload flow only)
from rag.pipeline import load_and_index_pdf
```

No other member should import from `rag/` directly. The orchestrator goes through `agents/retrieval_agent.py`, not `rag/pipeline.py`. If someone asks you to change a function signature, discuss it in the team channel first.

---

### Member 3 — Zeynep Çavuş (Retrieval Agent & Vector DB Specialist)

**Context:** Kerem built the full RAG infrastructure (`rag/`). Your job is two things: (1) write `agents/retrieval_agent.py` — the agent wrapper the orchestrator calls, and (2) extend and harden the embedding layer with metadata and a singleton fix.

#### Files you own
- `agents/retrieval_agent.py` ← **primary deliverable — create from scratch**
- `rag/embedder.py` (extend Kerem's)
- `rag/retriever.py` (extend Kerem's)
- `tests/test_retrieval.py`

#### Step-by-step tasks

**Task 0 — Write `agents/retrieval_agent.py` (do this first)**

The Retrieval Agent is the first agent the orchestrator calls. It wraps `rag/pipeline.search()` and gives the rest of the system a clean, agent-style interface. If the RAG layer ever changes internally, only this file needs updating.

```python
# agents/retrieval_agent.py
from rag.pipeline import search

def retrieve(question: str, k: int = 3) -> list[str]:
    """
    Retrieval Agent — finds the most relevant document chunks for a question.

    Args:
        question: The student's question.
        k:        Number of chunks to return (default 3).

    Returns:
        List of text strings ordered by relevance to the question.
        Returns empty list if no documents have been indexed yet.
    """
    if not question or not question.strip():
        return []

    chunks = search(question, k=k)
    return chunks
```

That's the base. The orchestrator imports `from agents.retrieval_agent import retrieve` and calls it first in the pipeline.

**Task 1 — Add metadata to chunks (modify `rag/embedder.py`)**

Kerem's current embedder stores chunks without metadata. You need to add source filename, page number, and chunk index so the UI can show "Source: lecture3.pdf, page 5".

```python
# rag/embedder.py — your additions
def embed_and_store_chunks(chunks: list, source_filename: str = "unknown") -> None:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Attach metadata to each chunk before storing
    for i, chunk in enumerate(chunks):
        chunk.metadata["source_file"] = source_filename
        chunk.metadata["chunk_index"] = i
        # page number is already set by PyPDFLoader as chunk.metadata["page"]

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION,
    )
```

Also update `rag/pipeline.py`'s `load_and_index_pdf()` to pass `source_filename`. **Coordinate with Kerem before changing `pipeline.py`.**

**Task 2 — Add document delete/replace (modify `rag/embedder.py`)**

If the user uploads a second PDF, the old chunks should be cleared first:

```python
def clear_collection() -> None:
    """Remove all documents from the vector store."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )
    db.delete_collection()
```

Expose this in `rag/pipeline.py` as `clear_index()`. Coordinate with Kerem.

**Task 3 — Fix the embedding singleton problem**

Kerem's code instantiates `HuggingFaceEmbeddings` inside every function call. This reloads the 90MB model from disk on each request. Fix it with a module-level singleton:

```python
# rag/embedder.py — add at top
_embeddings = None

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings
```

Apply the same fix in `rag/retriever.py`. This makes subsequent queries 5–10x faster.

**Task 4 — Update `retriever.py` to return metadata too**

Change the return type so callers can show source info:

```python
def retrieve_top_chunks(question: str, k: int = 3) -> list[dict]:
    """Returns list of {text, source_file, page, chunk_index}"""
    db = Chroma(persist_directory=CHROMA_DIR, embedding_function=_get_embeddings(), collection_name=COLLECTION)
    results = db.similarity_search(question, k=k)
    return [
        {
            "text": doc.page_content,
            "source_file": doc.metadata.get("source_file", "unknown"),
            "page": doc.metadata.get("page", 0),
            "chunk_index": doc.metadata.get("chunk_index", 0),
        }
        for doc in results
    ]
```

**Coordinate with Kerem** — this changes `search()` return type from `list[str]` to `list[dict]`. All agents using `chunks` will need updating. Discuss with the team first.

**Task 5 — Write `tests/test_retrieval.py`**

```python
# tests/test_retrieval.py
import os, pytest
from rag.pipeline import load_and_index_pdf, search

SAMPLE_PDF = "data/sample.pdf"  # put a real PDF here

@pytest.fixture(scope="module", autouse=True)
def index_sample():
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF found at data/sample.pdf")
    load_and_index_pdf(SAMPLE_PDF)

def test_search_returns_results():
    results = search("What is this document about?")
    assert len(results) > 0

def test_search_returns_strings():
    results = search("explain the main concept")
    assert all(isinstance(r, str) for r in results)  # or dict after your change

def test_search_top_k():
    results = search("any topic", k=5)
    assert len(results) <= 5

def test_search_empty_query():
    results = search("")
    # Should not crash — may return empty or random chunks
    assert isinstance(results, list)
```

#### Checklist
- [x] `agents/retrieval_agent.py` created — `retrieve()` function working
- [x] `retrieve("")` returns empty list without crashing
- [x] Embedding singleton (no model reload per call)
- [x] Metadata (source_file, page, chunk_index) stored in ChromaDB
- [x] `clear_collection()` / `clear_index()` working
- [x] `retriever.py` returns metadata (after team agreement on contract change)
- [x] `tests/test_retrieval.py` passing

#### Completed Work — Zeynep Çavuş

- Implemented `agents/retrieval_agent.py` as a clean interface for the RAG pipeline with safe handling of empty inputs.  
- Extended `rag/embedder.py` with metadata (`source_file`, `chunk_index`) and added `clear_collection()` (exposed as `clear_index()` in pipeline).  
- Applied singleton pattern in `embedder.py` and `retriever.py` to improve performance.  
- Updated retrieval logic to return metadata-aware results (`text`, `source_file`, `page`, `chunk_index`).  
- Developed and validated a test suite for the retrieval layer (all tests passing).  

⚠️ Note: Retrieval output changed from `list[str]` to `list[dict]`; downstream components should use `chunk["text"]`.

---

### Member 4 — Answer Agent Developer - Ezgi

**Context:** Kerem wrote a minimal `agents/answer_agent.py`. It works but it is a single-function stub with a hardcoded prompt and no Turkish support. Your job is to build the full Answer Agent on top of his base.

#### Files you own
- `agents/answer_agent.py` (extend Kerem's)
- `tests/test_answer.py`

#### Step-by-step tasks

**Task 1 — Understand Kerem's base**

```python
# What Kerem wrote — keep this function signature
def generate_answer(question: str, chunks: list[str]) -> str:
    ...
```

The orchestrator calls `generate_answer(question, chunks)` and expects a `str` back. **Do not change this signature.**

**Task 2 — Add language detection and prompt templates**

```python
# agents/answer_agent.py
import os
from langchain_ollama import OllamaLLM

_ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm = OllamaLLM(model="qwen2.5:7b", base_url=_ollama_host)

SYSTEM_PROMPT_TR = """Sen akademik bir asistansın. Yalnızca aşağıdaki bağlamı kullanarak soruyu yanıtla.
Bağlamda cevap yoksa "Bu soruyu yanıtlamak için yeterli bilgiye sahip değilim." de.
Madde işaretleri veya numaralı liste kullanarak yanıtla."""

SYSTEM_PROMPT_EN = """You are a helpful academic assistant.
Answer the student's question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."
Format your answer with bullet points or numbered steps where appropriate."""

def _detect_language(text: str) -> str:
    """Simple heuristic: if Turkish characters present, return 'tr'."""
    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    return "tr" if any(c in turkish_chars for c in text) else "en"

def _build_prompt(question: str, context: str, lang: str) -> str:
    system = SYSTEM_PROMPT_TR if lang == "tr" else SYSTEM_PROMPT_EN
    return f"""{system}

---
CONTEXT:
{context}
---

QUESTION: {question}

ANSWER:"""

def generate_answer(question: str, chunks: list[str]) -> str:
    context = "\n\n".join(chunks)
    lang = _detect_language(question)
    prompt = _build_prompt(question, context, lang)
    return llm.invoke(prompt)
```

**Task 3 — Add response format control**

Add an optional `format` parameter for future use:
```python
def generate_answer(question: str, chunks: list[str], format: str = "auto") -> str:
    # format: "auto" | "bullets" | "paragraph"
    # "auto" = let the LLM decide based on question type
```

**Task 4 — Write `tests/test_answer.py`**

These tests mock the LLM so they do not need Ollama running:

```python
# tests/test_answer.py
from unittest.mock import patch, MagicMock
from agents.answer_agent import generate_answer, _detect_language

def test_language_detection_turkish():
    assert _detect_language("Bunu açıklar mısın?") == "tr"

def test_language_detection_english():
    assert _detect_language("What is machine learning?") == "en"

def test_generate_answer_returns_string():
    with patch("agents.answer_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = "Machine learning is..."
        result = generate_answer("What is ML?", ["ML is a field of AI."])
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_answer_uses_context():
    with patch("agents.answer_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = "mocked"
        generate_answer("test?", ["chunk1", "chunk2"])
        call_args = mock_llm.invoke.call_args[0][0]
        assert "chunk1" in call_args
        assert "chunk2" in call_args

def test_generate_answer_empty_chunks():
    with patch("agents.answer_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = "I don't have enough information."
        result = generate_answer("What is X?", [])
    assert isinstance(result, str)
```

#### Checklist
- [x] `generate_answer()` signature unchanged (backward compatible)
- [x] Turkish + English prompt templates
- [x] Language auto-detection
- [x] Prompt includes all chunks as context block
- [x] `tests/test_answer.py` — all tests pass without Ollama (use mocks)

---

### Member 5 — Monitor Agent Developer - Aykut Akkuş

**Your job:** Build `agents/monitor_agent.py` from scratch. This agent receives the LLM's answer and the source chunks, then decides if the answer is trustworthy.

#### Files you own
- `agents/monitor_agent.py`
- `tests/test_monitor.py`

#### Step-by-step tasks

**Task 1 — Understand what you receive and must return**

```python
# Input:
answer: str       # the LLM's generated answer
chunks: list[str] # the source chunks used to generate it
question: str     # the original student question

# Output must be exactly:
{
    "passed": bool,       # True = safe to show, False = regenerate
    "flags": list[str],   # list of issues found (empty if clean)
    "answer": str         # return answer as-is (or cleaned version)
}
```

**Task 2 — Implement `agents/monitor_agent.py`**

```python
# agents/monitor_agent.py
import re

# Keywords that signal unsafe/irrelevant content
UNSAFE_PATTERNS = [
    r"\b(harm|kill|weapon|illegal|drug|hack)\b",
    r"<script",
    r"ignore previous instructions",
]

def _check_safety(answer: str) -> list[str]:
    """Return list of safety flags found in the answer."""
    flags = []
    text = answer.lower()
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(f"unsafe_pattern:{pattern}")
    return flags

def _check_grounding(answer: str, chunks: list[str]) -> list[str]:
    """
    Check if the answer contains claims that cannot be traced back to the chunks.
    Strategy: extract key noun phrases from the answer; check if at least
    MIN_OVERLAP% of them appear in the chunks.
    """
    flags = []
    if not chunks:
        flags.append("no_context_available")
        return flags

    combined_context = " ".join(chunks).lower()
    answer_words = set(re.findall(r'\b\w{5,}\b', answer.lower()))  # words ≥5 chars
    context_words = set(re.findall(r'\b\w{5,}\b', combined_context))

    if not answer_words:
        return flags

    overlap = len(answer_words & context_words) / len(answer_words)
    if overlap < 0.25:  # less than 25% of answer's significant words in source
        flags.append("low_source_overlap")

    return flags

def _check_refusal(answer: str) -> list[str]:
    """Flag if the LLM refused to answer (may mean the question is unanswerable)."""
    refusal_phrases = [
        "i don't have enough information",
        "yeterli bilgiye sahip değilim",
        "cannot answer",
        "unable to answer",
    ]
    text = answer.lower()
    for phrase in refusal_phrases:
        if phrase in text:
            return ["llm_refused"]
    return []

def check_answer(answer: str, chunks: list[str], question: str) -> dict:
    """
    Run all monitor checks. Returns a result dict that the orchestrator uses.
    """
    flags = []
    flags.extend(_check_safety(answer))
    flags.extend(_check_grounding(answer, chunks))
    flags.extend(_check_refusal(answer))

    # Answer fails if there are any hard flags (safety issues)
    safety_flags = [f for f in flags if f.startswith("unsafe")]
    passed = len(safety_flags) == 0

    return {
        "passed": passed,
        "flags": flags,
        "answer": answer,
    }
```

**Task 3 — Add logging**

```python
import logging

logger = logging.getLogger("monitor_agent")

def check_answer(answer: str, chunks: list[str], question: str) -> dict:
    result = ...  # your implementation above
    if result["flags"]:
        logger.warning("Monitor flags: %s | Q: %s", result["flags"], question[:80])
    return result
```

**Task 4 — Write `tests/test_monitor.py`**

```python
# tests/test_monitor.py
from agents.monitor_agent import check_answer, _check_safety, _check_grounding

SAMPLE_CHUNKS = [
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by biological neurons.",
]

def test_clean_answer_passes():
    answer = "Machine learning is a subset of AI."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is ML?")
    assert result["passed"] is True
    assert result["answer"] == answer

def test_unsafe_content_fails():
    answer = "You should hack the system to learn faster."
    result = check_answer(answer, SAMPLE_CHUNKS, "How to learn?")
    assert result["passed"] is False
    assert any("unsafe" in f for f in result["flags"])

def test_low_grounding_flagged():
    answer = "Quantum entanglement destroys parallel universes instantly."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is entanglement?")
    # Should have low_source_overlap flag
    assert "low_source_overlap" in result["flags"]

def test_refusal_detected():
    answer = "I don't have enough information to answer that."
    result = check_answer(answer, SAMPLE_CHUNKS, "What is X?")
    assert "llm_refused" in result["flags"]

def test_empty_chunks_flagged():
    result = check_answer("Some answer.", [], "Question?")
    assert "no_context_available" in result["flags"]

def test_result_structure():
    result = check_answer("test answer", SAMPLE_CHUNKS, "test?")
    assert "passed" in result
    assert "flags" in result
    assert "answer" in result
    assert isinstance(result["flags"], list)
```

#### Checklist
- [x] `check_answer()` returns exact dict contract
- [x] Safety pattern matching (regex)
- [x] Source grounding check (overlap heuristic)
- [x] Refusal detection
- [x] Logging for flagged answers
- [x] `tests/test_monitor.py` — all pass without LLM

---

### Member 6 — Evaluator Agent & Test Lead - Yağız Efe Gökçe

**Your job has two parts:** (A) Build `agents/evaluator_agent.py`, and (B) own all integration and coverage testing.

#### Files you own
- `agents/evaluator_agent.py`
- `tests/test_evaluator.py`
- `tests/test_integration.py`

#### Step-by-step tasks

**Task 1 — Implement `agents/evaluator_agent.py`**

The evaluator calls the LLM to score the answer. It does NOT need a human-written reference answer — it judges quality based on the question + context alone.

```python
# agents/evaluator_agent.py
import os, json, re
from langchain_ollama import OllamaLLM

_ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm = OllamaLLM(model="qwen2.5:7b", base_url=_ollama_host)

EVAL_PROMPT = """You are an academic answer evaluator. Score the following answer on three criteria.
Return ONLY valid JSON — no explanation, no markdown, just raw JSON.

Question: {question}

Context (source material):
{context}

Answer to evaluate:
{answer}

Score each criterion from 0 to 10:
- relevance: Does the answer address the question?
- accuracy: Is the answer factually consistent with the context?
- completeness: Does the answer cover the key points in the context?

Return exactly this JSON:
{{"relevance": <number>, "accuracy": <number>, "completeness": <number>, "feedback": "<one sentence>"}}"""

def _parse_scores(raw: str) -> dict:
    """Parse JSON from LLM output. Fallback to zeros if malformed."""
    try:
        # Strip markdown code blocks if LLM wraps with them
        cleaned = re.sub(r"```[a-z]*", "", raw).strip()
        data = json.loads(cleaned)
        return {
            "relevance": float(data.get("relevance", 0)),
            "accuracy": float(data.get("accuracy", 0)),
            "completeness": float(data.get("completeness", 0)),
            "feedback": str(data.get("feedback", "")),
        }
    except (json.JSONDecodeError, ValueError):
        return {"relevance": 0.0, "accuracy": 0.0, "completeness": 0.0, "feedback": "parse_error"}

def evaluate_answer(question: str, answer: str, chunks: list[str]) -> dict:
    """
    Score the answer using the LLM as a judge.

    Returns:
        {score, relevance, accuracy, completeness, feedback}
    """
    context = "\n\n".join(chunks)
    prompt = EVAL_PROMPT.format(question=question, context=context, answer=answer)
    raw = llm.invoke(prompt)
    scores = _parse_scores(raw)
    scores["score"] = round((scores["relevance"] + scores["accuracy"] + scores["completeness"]) / 3, 2)
    return scores
```

**Task 2 — Write `tests/test_evaluator.py`**

```python
# tests/test_evaluator.py
from unittest.mock import patch
from agents.evaluator_agent import evaluate_answer, _parse_scores
import json

def test_parse_scores_valid_json():
    raw = '{"relevance": 8, "accuracy": 7, "completeness": 6, "feedback": "Good answer."}'
    result = _parse_scores(raw)
    assert result["relevance"] == 8.0
    assert result["feedback"] == "Good answer."

def test_parse_scores_with_code_block():
    raw = '```json\n{"relevance": 9, "accuracy": 8, "completeness": 7, "feedback": "ok"}\n```'
    result = _parse_scores(raw)
    assert result["relevance"] == 9.0

def test_parse_scores_malformed():
    result = _parse_scores("not json at all")
    assert result["score_"] == 0.0 or result["relevance"] == 0.0  # fallback

def test_evaluate_answer_returns_score():
    mock_response = json.dumps({
        "relevance": 8, "accuracy": 9, "completeness": 7, "feedback": "Well done."
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("What is ML?", "ML is AI.", ["ML is artificial intelligence."])
    assert "score" in result
    assert 0.0 <= result["score"] <= 10.0

def test_score_is_average():
    mock_response = json.dumps({
        "relevance": 9, "accuracy": 6, "completeness": 3, "feedback": "ok"
    })
    with patch("agents.evaluator_agent.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = evaluate_answer("q", "a", ["c"])
    assert result["score"] == round((9 + 6 + 3) / 3, 2)
```

**Task 3 — Write `tests/test_integration.py`**

This test requires Ollama running. Skip gracefully if not available.

```python
# tests/test_integration.py
import os, pytest

SAMPLE_PDF = "data/sample.pdf"

@pytest.fixture(scope="module")
def indexed_pdf():
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip("No sample PDF at data/sample.pdf")
    from rag.pipeline import load_and_index_pdf
    load_and_index_pdf(SAMPLE_PDF)

def test_full_pipeline(indexed_pdf):
    """End-to-end test: index → search → answer → monitor → evaluate"""
    try:
        from orchestrator.pipeline import run_pipeline
        result = run_pipeline("What is the main topic of this document?")
        assert result["answer"]
        assert isinstance(result["score"], float)
        assert isinstance(result["flags"], list)
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")

def test_pipeline_result_structure(indexed_pdf):
    try:
        from orchestrator.pipeline import run_pipeline
        result = run_pipeline("Summarize the key points.")
        required_keys = ["answer", "score", "breakdown", "flags", "chunks", "attempts"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")
```

**Task 4 — Set up pytest + coverage**

Add to `requirements.txt`:
```
pytest
pytest-cov
```

Run all tests:
```bash
pytest tests/ -v --cov=agents --cov=rag --cov=orchestrator --cov-report=term-missing
```

Add a `Makefile` or `scripts/run_tests.sh`:
```bash
#!/bin/bash
pytest tests/ -v --cov=agents --cov=rag --cov=orchestrator --cov-report=html
echo "Coverage report at htmlcov/index.html"
```

#### Checklist
- [x] `evaluate_answer()` returns exact dict contract with `score`
- [x] JSON parsing with fallback (LLM sometimes returns markdown)
- [x] `tests/test_evaluator.py` — all pass without Ollama (use mocks)
- [x] `tests/test_integration.py` — skips gracefully if Ollama not running
- [x] pytest + coverage configured
- [x] Coverage target: ≥ 70% across agents/ and rag/

---

### Member 7 — Zeynep Uygur (UI/UX Developer — Streamlit)

**Context:** Kerem wrote `app.py` as a minimal skeleton. Your job is to migrate and expand it into a full chat interface at `ui/app.py`. Do not delete `app.py` from the root until the migration is confirmed working.

#### Files you own
- `ui/app.py` (new — your full implementation)
- `ui/components/` (optional: extract reusable widgets here)

#### Step-by-step tasks

**Task 1 — Study Kerem's skeleton**

Kerem's `app.py` does:
1. File upload → `load_and_index_pdf()`
2. Text input → `search()` + `generate_answer()`
3. Displays raw answer + chunk expander

You will replace `generate_answer()` + raw chunks with `run_pipeline()` from the orchestrator. This gives you access to score, flags, and breakdown automatically.

**Task 2 — Write `ui/app.py`**

```python
# ui/app.py
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from rag.pipeline import load_and_index_pdf
from orchestrator.pipeline import run_pipeline

st.set_page_config(page_title="EduAgent", page_icon="📚", layout="wide")

# ── Session state initialization ──────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []   # list of {question, answer, score, flags}
if "pdf_indexed" not in st.session_state:
    st.session_state.pdf_indexed = False

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title("📚 EduAgent")
    st.caption("Academic AI Assistant")
    st.divider()

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file:
        if st.button("Process Document", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            with st.spinner("Indexing document..."):
                load_and_index_pdf(tmp_path)
            st.session_state.pdf_indexed = True
            st.success("Ready! Ask your question.")

    if st.session_state.pdf_indexed:
        st.success("Document loaded ✓")

    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()

# ── Main area ─────────────────────────────────────────────────
st.title("EduAgent — Academic Assistant")

if not st.session_state.pdf_indexed:
    st.info("Upload and process a PDF from the sidebar to get started.")
else:
    # Render chat history
    for entry in st.session_state.history:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.write(entry["answer"])
            _render_score_badge(entry["score"])
            if entry.get("flags"):
                st.warning(f"Flags: {', '.join(entry['flags'])}")

    # Chat input
    question = st.chat_input("Ask a question about your document...")
    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = run_pipeline(question)

            st.write(result["answer"])
            _render_score_badge(result["score"])

            if result.get("flags"):
                st.warning(f"Monitor flags: {', '.join(result['flags'])}")

            with st.expander("Score breakdown"):
                breakdown = result.get("breakdown", {})
                col1, col2, col3 = st.columns(3)
                col1.metric("Relevance", f"{breakdown.get('relevance', 0):.1f}/10")
                col2.metric("Accuracy", f"{breakdown.get('accuracy', 0):.1f}/10")
                col3.metric("Completeness", f"{breakdown.get('completeness', 0):.1f}/10")
                if result.get("feedback"):
                    st.caption(result["feedback"])
                st.caption(f"Attempts: {result.get('attempts', 1)}")

            with st.expander("Source chunks"):
                for i, chunk in enumerate(result.get("chunks", []), 1):
                    st.markdown(f"**Chunk {i}**")
                    st.write(chunk)

        st.session_state.history.append({
            "question": question,
            "answer": result["answer"],
            "score": result["score"],
            "flags": result.get("flags", []),
        })


def _render_score_badge(score: float):
    """Display a colored score badge."""
    color = "green" if score >= 7 else "orange" if score >= 4 else "red"
    st.markdown(
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:12px;">Score: {score:.1f}/10</span>',
        unsafe_allow_html=True,
    )
```

> **Note:** Move `_render_score_badge` to the top of the file (define before use), or put it in `ui/components/score_badge.py`.

**Task 3 — Run with Docker**

Update `docker-compose.yml` so it runs `ui/app.py` instead of `app.py`:
```yaml
command: streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
```
Coordinate with Kerem if Docker config needs to change.

**Task 4 — UX polish**

- Color theme: set a dark or academic color palette in `.streamlit/config.toml`:
  ```toml
  [theme]
  primaryColor = "#2E86AB"
  backgroundColor = "#F5F5F5"
  secondaryBackgroundColor = "#FFFFFF"
  textColor = "#1A1A2E"
  ```
- Ensure sidebar collapses on mobile (Streamlit handles this with `layout="wide"`)
- Add a "New Conversation" button that clears history without re-indexing

#### Checklist
- [x] `ui/app.py` — full chat bubble interface
- [x] Session history persists across messages in same session
- [x] Score badge rendered per answer
- [x] Score breakdown expander
- [x] Source chunks expander
- [x] Monitor flags displayed as warning
- [x] Sidebar: upload, process, status
- [x] Color theme configured
- [x] Docker command updated to point at `ui/app.py`

---

## 5. Kerem's Work — Review

### What's done and done well

| File | Status | Notes |
|------|--------|-------|
| `rag/loader.py` | ✅ Clean | PyPDFLoader + RecursiveCharacterTextSplitter |
| `rag/embedder.py` | ✅ Working | HuggingFace all-MiniLM-L6-v2, no API key needed |
| `rag/retriever.py` | ✅ Working | ChromaDB similarity search |
| `rag/pipeline.py` | ✅ Excellent | Single entry point, great design decision |
| `agents/answer_agent.py` | ✅ Working stub | Ollama integration works, needs extension |
| `app.py` | ✅ Skeleton | Works for demo, Member 7 takes it from here |
| `Dockerfile` | ✅ | App + Ollama services |
| `docker-compose.yml` | ✅ | Correct OLLAMA_HOST env var |
| `requirements.txt` | ✅ | All dependencies listed |

### Open questions for Kerem — ANSWERED

The questions below have been resolved during implementation. They are kept here for reference.

**Q1 — Model name:** ✅ Resolved. The codebase uses `qwen2.5:7b` everywhere (agents, tests, docker-compose comments). Update your local Ollama with `ollama pull qwen2.5:7b`.

**Q2 — File naming:** ✅ Resolved. The team kept Kerem's naming (`loader.py`, `embedder.py`, `retriever.py`). No additional wrappers were needed.

**Q3 — Collection isolation:** ✅ Resolved. `rag/embedder.py` provides `clear_collection()` and `rag/pipeline.py` exposes it as `clear_index()`. The UI and integration tests call `clear_index()` before indexing a new PDF, so old chunks are wiped. Multi-doc indexing is still possible by skipping `clear_index()`.

**Q4 — Metadata:** ✅ Resolved. `rag/embedder.py` stores `source_file`, `page`, and `chunk_index` on every chunk. `rag/retriever.py` returns these fields in `retrieve_top_chunks()`. The UI shows source metadata.

**Q5 — Return type change:** ✅ Resolved. `search()` now returns `list[dict]` with `text`, `source_file`, `page`, `chunk_index`. All downstream agents (`answer_agent.py`, `monitor_agent.py`, `evaluator_agent.py`) have been updated to handle dict chunks gracefully, including backward-compatible string chunk support.

---

## 6. Integration Checklist (Member 1 signs off)

Before the final demo, confirm every item below works end-to-end:

- [ ] `docker compose up --build` starts cleanly with no errors
- [ ] `docker exec -it eduagent-ollama ollama pull qwen2.5:7b` downloads the model
- [ ] Upload `data/sample.pdf` → "Process Document" succeeds
- [ ] Ask a question → full pipeline runs (RAG → Answer → Monitor → Evaluate)
- [ ] Score badge appears on answer
- [ ] Score breakdown expander shows three numbers
- [ ] Monitor flags appear if triggered
- [ ] Chat history persists within the session
- [x] `pytest tests/ -v` runs with ≥ 70% of unit tests passing (Ollama-dependent tests skip)
- [ ] `pytest tests/test_integration.py` passes when Ollama is running

---

## 7. Dependency Rules (No Circular Imports)

```
Allowed import directions (→ = "may import from"):

ui/app.py                    → orchestrator/pipeline.py
orchestrator/pipeline.py     → agents/*   (ALL 4 agents — retrieval, answer, monitor, evaluator)
agents/retrieval_agent.py    → rag/pipeline.py
agents/answer_agent.py       → (external libs only — langchain, ollama)
agents/monitor_agent.py      → (external libs only — re, logging)
agents/evaluator_agent.py    → (external libs only — langchain, ollama)
rag/pipeline.py              → rag/loader, rag/embedder, rag/retriever
rag/loader                   → (external libs only)
rag/embedder                 → (external libs only)
rag/retriever                → (external libs only)

NEVER:
orchestrator/ → rag/*        (orchestrator goes through agents, not rag directly)
agents/*      → agents/*     (agents do not call each other — orchestrator does that)
rag/*         → agents/*     (RAG layer is unaware of agents)
```

---

## 8. Sprint Schedule

| Week | Focus | Owner |
|------|-------|-------|
| 1 | Repo setup, branch strategy, Kerem's answers to Q1-Q5, metadata fix, Ezgi's prompt templates | Murat, Kerem, Zeynep Ç., Ezgi |
| 2 | Monitor agent, Evaluator agent, orchestrator pipeline | Aykut, Yağız, Murat |
| 3 | UI chat interface, integration wiring, Docker update | Zeynep Uygur, Murat, all |
| 4 | Full test suite, smoke test, demo prep, README | Yağız, Murat, all |

---

*EduAgent — 7-Person Team · April 2026*
