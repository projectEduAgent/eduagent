# ui/app.py — EduAgent
# Run with: streamlit run ui/app.py

import sys
import os
import tempfile

# Ensure the project root is on the path so we can import agents and rag
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from rag.pipeline import load_and_index_pdf, clear_index
from orchestrator.pipeline import run_pipeline

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="EduAgent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background: #0b0d17;
    color: #e2e4f0;
}

header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background: radial-gradient(ellipse at 10% 0%, #1a1040 0%, #0b0d17 55%),
                radial-gradient(ellipse at 90% 100%, #0d1f3a 0%, transparent 60%);
    min-height: 100vh;
}

.header-wrap {
    text-align: center;
    padding: 2.5rem 1rem 2rem;
}

.header-badge {
    display: inline-block;
    background: linear-gradient(135deg, #7c3aed22, #3b82f622);
    border: 1px solid #7c3aed55;
    border-radius: 20px;
    padding: 0.25rem 1rem;
    font-size: 0.72rem;
    color: #a78bfa;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 1rem;
}

.header-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #c4b5fd 0%, #818cf8 40%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
    letter-spacing: -1px;
}

.header-sub {
    color: #6b7280;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

.header-divider {
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #7c3aed, #38bdf8);
    border-radius: 2px;
    margin: 1.2rem auto 0;
}

.upload-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #7c3aed;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.5rem;
}

.active-doc {
    background: linear-gradient(135deg, #05300520, #1a3a2a40);
    border: 1px solid #22c55e33;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    margin-top: 0.8rem;
}

.active-doc-label {
    font-size: 0.68rem;
    color: #22c55e;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.2rem;
}

.active-doc-name {
    font-size: 0.9rem;
    color: #e2e4f0;
    font-weight: 500;
}

.agent-arch-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #7c3aed;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.8rem;
}

.agent-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.6rem 0.8rem;
    border-radius: 10px;
    margin-bottom: 0.4rem;
    background: #ffffff06;
    border: 1px solid #ffffff0a;
}

.agent-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 0.05rem; }
.agent-name { font-size: 0.82rem; font-weight: 600; color: #c4b5fd; display: block; }
.agent-desc { font-size: 0.72rem; color: #6b7280; display: block; margin-top: 0.1rem; }

.chat-section-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 1rem;
}

.msg-user-wrap { display: flex; justify-content: flex-end; margin: 0.6rem 0; }
.msg-user {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.1rem;
    max-width: 72%;
    font-size: 0.9rem;
    color: #f0eeff;
    box-shadow: 0 4px 20px #7c3aed33;
}

.msg-agent-wrap { display: flex; justify-content: flex-start; margin: 0.6rem 0; }
.msg-agent {
    background: linear-gradient(135deg, #111827, #0f172a);
    border: 1px solid #ffffff14;
    border-radius: 4px 18px 18px 18px;
    padding: 0.75rem 1.1rem;
    max-width: 85%;
    font-size: 0.88rem;
    color: #d1d5db;
    line-height: 1.6;
    box-shadow: 0 4px 20px #00000044;
}

.msg-label {
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.35rem;
    opacity: 0.6;
}

.scores-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    margin: 0.8rem 0;
}

.score-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 0.75rem 0.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.score-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}

.sc-overall::before { background: linear-gradient(90deg, #7c3aed, #38bdf8); }
.sc-rel::before     { background: linear-gradient(90deg, #22c55e, #16a34a); }
.sc-acc::before     { background: linear-gradient(90deg, #3b82f6, #2563eb); }
.sc-comp::before    { background: linear-gradient(90deg, #f59e0b, #d97706); }

.score-val {
    font-size: 1.7rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    display: block;
    line-height: 1;
}

.score-lbl {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #6b7280;
    margin-top: 0.3rem;
    font-weight: 600;
    display: block;
}

.sv-high { color: #4ade80; }
.sv-mid  { color: #fbbf24; }
.sv-low  { color: #f87171; }

.monitor-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
    margin: 0.5rem 0;
}

.monitor-label {
    font-size: 0.65rem;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    border-radius: 8px;
    padding: 0.2rem 0.55rem;
    font-size: 0.68rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.badge-warn { background: #45180340; border: 1px solid #d9770655; color: #fbbf24; }
.badge-ok   { background: #05300530; border: 1px solid #22c55e44; color: #4ade80; }

.feedback-box {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-left: 3px solid #7c3aed;
    border-radius: 0 10px 10px 0;
    padding: 0.55rem 0.85rem;
    font-size: 0.78rem;
    color: #94a3b8;
    margin: 0.5rem 0;
    font-style: italic;
}

.chunk-item {
    background: #0f172a;
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 0.8rem;
    margin: 0.4rem 0;
}

.chunk-meta {
    font-size: 0.65rem;
    color: #3b82f6;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.3rem;
}

.chunk-text { font-size: 0.78rem; color: #64748b; line-height: 1.5; }

.pipeline-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.8rem;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    margin: 0.8rem 0;
    flex-wrap: wrap;
}

.pip-step {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}

.pip-wait { background:#1e2230; color:#4b5563; border:1px solid #374151; }
.pip-run  { background:#1e3a5f; color:#60a5fa; border:1px solid #3b82f6; animation: pulse 1s infinite; }
.pip-done { background:#14532d; color:#4ade80; border:1px solid #22c55e; }
.pip-arrow { color:#374151; font-size:0.8rem; }

@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }

.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 12px !important;
    color: #e2e4f0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px #7c3aed22 !important;
}

.stButton > button {
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    box-shadow: 0 4px 15px #7c3aed44 !important;
}

.stButton > button[kind="secondary"] {
    background: #1f2937 !important;
    color: #9ca3af !important;
}

hr {
    border: none !important;
    border-top: 1px solid #1f2937 !important;
    margin: 1.2rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="header-wrap">
    <div class="header-badge">🎓 Multi-Agent AI System</div>
    <h1 class="header-title">EduAgent</h1>
    <p class="header-sub">Academic Assistant · RAG-Based Multi-Agent AI</p>
    <div class="header-divider"></div>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_indexed" not in st.session_state:
    st.session_state.pdf_indexed = False
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

# ── Layout ─────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2.2], gap="large")

# ══════════════════════════════════════════════════════════════
# LEFT COLUMN
# ══════════════════════════════════════════════════════════════
with col_left:

    st.markdown('<div class="upload-label">📄 Upload Document</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file:
        st.markdown(
            f"<div style='font-size:0.82rem;color:#94a3b8;margin:0.4rem 0;'>"
            f"📎 <b style='color:#e2e4f0;'>{uploaded_file.name}</b></div>",
            unsafe_allow_html=True,
        )

        if st.button("⚡ Process & Index PDF", use_container_width=True, type="primary"):
            tmp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(tmp_path, 'wb') as tmp:
                tmp.write(uploaded_file.read())

            with st.spinner("Chunking and indexing into ChromaDB…"):
                clear_index()
                load_and_index_pdf(tmp_path)

            st.session_state.pdf_indexed = True
            st.session_state.pdf_name = uploaded_file.name
            st.session_state.chat_history = []
            st.success("✅ Indexed successfully!")

    if st.session_state.pdf_indexed:
        st.markdown(f"""
        <div class="active-doc">
            <div class="active-doc-label">✅ Active Document</div>
            <div class="active-doc-name">{st.session_state.pdf_name}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown('<div class="agent-arch-title">🤖 Agent Architecture</div>', unsafe_allow_html=True)

    for icon, name, desc in [
        ("🔍", "Retrieval Agent",  "Fetches relevant chunks from ChromaDB"),
        ("💬", "Answer Agent",     "Generates answer via Ollama LLM"),
        ("🛡️", "Monitor Agent",    "Safety & hallucination check"),
        ("📊", "Evaluator Agent",  "Scores answer quality (0–10)"),
    ]:
        st.markdown(f"""
        <div class="agent-item">
            <span class="agent-icon">{icon}</span>
            <div>
                <span class="agent-name">{name}</span>
                <span class="agent-desc">{desc}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    total_q = len(st.session_state.chat_history)
    if total_q > 0:
        avg = sum(e.get("scores", {}).get("score", 0) for e in st.session_state.chat_history) / total_q
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
            <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;
                        padding:0.8rem;text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:#c4b5fd;
                            font-family:'JetBrains Mono',monospace;">{total_q}</div>
                <div style="font-size:0.62rem;color:#6b7280;text-transform:uppercase;
                            letter-spacing:0.8px;font-weight:600;">Questions</div>
            </div>
            <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;
                        padding:0.8rem;text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:#38bdf8;
                            font-family:'JetBrains Mono',monospace;">{avg:.1f}</div>
                <div style="font-size:0.62rem;color:#6b7280;text-transform:uppercase;
                            letter-spacing:0.8px;font-weight:600;">Avg Score</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# RIGHT COLUMN
# ══════════════════════════════════════════════════════════════
with col_right:

    st.markdown('<div class="chat-section-title">💬 Questions & Answers</div>', unsafe_allow_html=True)

    for entry in st.session_state.chat_history:

        st.markdown(f"""
        <div class="msg-user-wrap">
            <div class="msg-user">
                <div class="msg-label" style="color:#c4b5fd88;">You</div>
                {entry["question"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        flags = entry.get("flags", [])
        passed = entry.get("passed", True)
        border = "#22c55e22" if passed else "#f8717122"

        st.markdown(f"""
        <div class="msg-agent-wrap">
            <div class="msg-agent" style="border-color:{border};">
                <div class="msg-label" style="color:#38bdf888;">EduAgent</div>
                {entry["answer"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("ℹ️ This answer was generated using retrieved document context.")

        scores = entry.get("scores", {})
        if scores:
            def sc(v):
                return "sv-high" if v >= 7 else ("sv-mid" if v >= 4 else "sv-low")

            overall = scores.get("score", 0)
            rel     = scores.get("relevance", 0)
            acc     = scores.get("accuracy", 0)
            comp    = scores.get("completeness", 0)

            st.markdown(f"""
            <div class="scores-row">
                <div class="score-card sc-overall">
                    <span class="score-val {sc(overall)}">{overall:.1f}</span>
                    <span class="score-lbl">Overall</span>
                </div>
                <div class="score-card sc-rel">
                    <span class="score-val {sc(rel)}">{rel:.1f}</span>
                    <span class="score-lbl">Relevance</span>
                </div>
                <div class="score-card sc-acc">
                    <span class="score-val {sc(acc)}">{acc:.1f}</span>
                    <span class="score-lbl">Accuracy</span>
                </div>
                <div class="score-card sc-comp">
                    <span class="score-val {sc(comp)}">{comp:.1f}</span>
                    <span class="score-lbl">Completeness</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            feedback = scores.get("feedback", "")
            if feedback and feedback != "parse_error":
                st.markdown(f'<div class="feedback-box">💡 {feedback}</div>', unsafe_allow_html=True)

        badges = "".join(f'<span class="badge badge-warn">⚠ {f}</span>' for f in flags) if flags \
                 else '<span class="badge badge-ok">✓ Safe</span>'

        st.markdown(f"""
        <div class="monitor-row">
            <span class="monitor-label">Monitor:</span>
            {badges}
        </div>
        """, unsafe_allow_html=True)

        if not passed:
            st.error("⚠️ **Monitor Alert:** This answer may contain unsafe content. Please review carefully.")
        elif flags:
            st.warning("⚠️ **Monitor Warning:** Answer may not be fully grounded in the source document. Verify before relying on it.")

        chunks = entry.get("chunks", [])
        if chunks:
            with st.expander(f"📎 Source chunks — {len(chunks)} retrieved", expanded=True):
                for i, chunk in enumerate(chunks, 1):
                    source_file = chunk.get("source_file", "unknown") if isinstance(chunk, dict) else "unknown"
                    page = chunk.get("page", "?") if isinstance(chunk, dict) else "?"
                    text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
                    st.markdown(f"""
                    <div class="chunk-item">
                        <div class="chunk-meta">#{i} · {source_file} · page {page}</div>
                        <div class="chunk-text">{text[:320]}{'…' if len(text) > 320 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Question input ────────────────────────────────────────
    if not st.session_state.pdf_indexed:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;">
            <div style="font-size:2.5rem;margin-bottom:0.8rem;">📄</div>
            <div style="font-size:0.9rem;color:#4b5563;font-weight:500;">Upload a PDF to get started</div>
            <div style="font-size:0.78rem;color:#374151;margin-top:0.3rem;">
                Your document will be indexed and ready to query
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        question = st.text_input(
            "question",
            placeholder="Ask anything about your document… e.g. What is Q-Learning?",
            label_visibility="collapsed",
            key="question_input",
        )

        c1, c2 = st.columns([4, 1])
        with c1:
            ask = st.button("🔍 Ask", use_container_width=True, type="primary")
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if ask:
            if not question.strip():
                st.warning("Please enter a question first.")
            else:
                pip_ph = st.empty()

                def show_pip(active: str):
                    steps = [("🔍","Retrieval"),("💬","Answer"),("🛡️","Monitor"),("📊","Evaluator")]
                    order = [s[1] for s in steps]
                    html  = '<div class="pipeline-wrap">'
                    for i, (icon, name) in enumerate(steps):
                        if name == active:
                            css, pre = "pip-run", "⟳ "
                        elif order.index(name) < order.index(active):
                            css, pre = "pip-done", "✓ "
                        else:
                            css, pre = "pip-wait", ""
                        html += f'<span class="pip-step {css}">{pre}{icon} {name}</span>'
                        if i < len(steps) - 1:
                            html += '<span class="pip-arrow">→</span>'
                    html += "</div>"
                    pip_ph.markdown(html, unsafe_allow_html=True)

                show_pip("Retrieval")

                # ── Run the full orchestrator pipeline ──────────────────
                result = run_pipeline(question)

                show_pip("Evaluator")

                pip_ph.empty()

                st.session_state.chat_history.append({
                    "question": question,
                    "answer":   result["answer"],
                    "chunks":   result.get("chunks", []),
                    "passed":   not any(f.startswith("unsafe_pattern:") for f in result.get("flags", [])),
                    "flags":    result.get("flags", []),
                    "scores":   {
                        "score":        result.get("score", 0.0),
                        "relevance":    result.get("breakdown", {}).get("relevance", 0.0),
                        "accuracy":     result.get("breakdown", {}).get("accuracy", 0.0),
                        "completeness": result.get("breakdown", {}).get("completeness", 0.0),
                        "feedback":     result.get("feedback", ""),
                    },
                })

                st.rerun()
