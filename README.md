# EduAgent — Multi-Agent Academic Assistant

EduAgent is a multi-agent academic assistant built for students and researchers. Users upload PDF documents; the system chunks, embeds, and stores them in a local vector database. When a student asks a question, four specialized agents work in sequence to produce a high-quality, grounded, verified answer.

The agent pipeline is: **Retrieval** → **Answer Generation** → **Monitor** → **Evaluation**. If the monitor flags safety issues or the evaluator score falls below the threshold, the orchestrator automatically retries answer generation (up to two attempts). The final answer, confidence score, and source chunks are presented in a clean Streamlit chat interface.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Streamlit UI)                         │
│   Upload PDF  ──►  Process  ──►  Ask Question  ──►  Read Answer    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              orchestrator/pipeline.py  (Member 1)                   │
│  Ties all agents together. Calls them in sequence, passes outputs. │
└──┬──────────────────────────────────────────────────────────────────┘
   │
   │  Step 1
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│           RAG Pipeline  (Kerem — Member 2) ✅ COMPLETE              │
│  rag/pipeline.py  →  load_and_index_pdf()  /  search()             │
│  Internally: loader → embedder → ChromaDB → retriever              │
└──┬──────────────────────────────────────────────────────────────────┘
   │  Step 2
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Answer Agent  (Member 4 — Ezgi)                        │
│  agents/answer_agent.py                                             │
│  Builds a rich prompt → calls Ollama LLM → returns answer string   │
└──┬──────────────────────────────────────────────────────────────────┘
   │  Step 3
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Monitor Agent  (Member 5 — Aykut Akkuş)               │
│  agents/monitor_agent.py                                            │
│  Checks answer for hallucinations, safety, source grounding        │
└──┬──────────────────────────────────────────────────────────────────┘
   │  Step 4
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Evaluator Agent  (Member 6 — Yağız Efe Gökçe)         │
│  agents/evaluator_agent.py                                          │
│  Scores answer on Relevance / Accuracy / Completeness (0-10)       │
│  Triggers retry loop if score < threshold (max 2 retries)          │
└──┬──────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Streamlit UI  (Member 7 — Zeynep Uygur)                │
│  ui/app.py                                                          │
│  Chat bubbles, score badge, source expander, session history       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (Docker)

The fastest way to run EduAgent is with Docker Compose. It starts the Streamlit app and a local Ollama server.

```bash
# Build and start
docker compose up --build

# In another terminal, pull the LLM model
docker exec -it eduagent-ollama ollama pull qwen2.5:7b
```

Then open http://localhost:8501 in your browser.

---

## Quick Start (Local)

Requires Python 3.12 and Ollama installed locally.

```bash
# 1. Install Ollama and pull the model
ollama pull qwen2.5:7b

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Streamlit UI
streamlit run ui/app.py
```

Then open http://localhost:8501 in your browser.

---

## Running Tests

Unit tests mock the LLM so they do not require Ollama running. Integration tests skip gracefully if Ollama is unavailable.

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=agents --cov=rag --cov=orchestrator --cov-report=term-missing
```

---

## Team

| Member | Role |
|--------|------|
| Murat | Project Manager & Orchestrator Developer |
| Kerem | RAG Pipeline Developer |
| Zeynep Çavuş | Retrieval Agent & Vector DB Specialist |
| Ezgi | Answer Agent Developer |
| Aykut Akkuş | Monitor Agent Developer |
| Yağız Efe Gökçe | Evaluator Agent & Test Lead |
| Zeynep Uygur | UI/UX Developer |

---

*EduAgent — 7-Person Team · April 2026*
