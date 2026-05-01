# agents/evaluator_agent.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Score an LLM-generated answer on three criteria
# (relevance, accuracy, completeness) using a local Ollama LLM as judge.
#
# How it works:
#   1. Receive the question, the answer, and the source chunks.
#   2. Build an evaluation prompt that asks the LLM to return JSON scores.
#   3. Parse the JSON (with markdown-code-block fallback) and compute
#      an overall score as the average of the three criteria.
#
# Depends on: Ollama running locally with qwen3.5:9b pulled.
#   → Start Ollama:   ollama serve
#   → Pull model:     ollama pull qwen3.5:9b
# ─────────────────────────────────────────────────────────────

import json
import os
import re

from langchain_ollama import OllamaLLM

_ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm = OllamaLLM(model="qwen3.5:9b", base_url=_ollama_host)

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


def _clamp_score(value) -> float:
    """Clamp a score to [0.0, 10.0] and coerce NaN/Inf to 0.0."""
    try:
        f = float(value)
        if f != f:  # NaN check
            return 0.0
        return max(0.0, min(10.0, f))
    except (ValueError, TypeError):
        return 0.0


def _parse_scores(raw: str) -> dict:
    """Parse JSON from LLM output. Fallback to zeros if malformed."""
    try:
        cleaned = re.sub(r"```[a-z]*", "", raw).strip()
        cleaned = cleaned.replace("```", "").strip()
        data = json.loads(cleaned)
        return {
            "relevance": _clamp_score(data.get("relevance", 0)),
            "accuracy": _clamp_score(data.get("accuracy", 0)),
            "completeness": _clamp_score(data.get("completeness", 0)),
            "feedback": str(data.get("feedback", "")),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "relevance": 0.0,
            "accuracy": 0.0,
            "completeness": 0.0,
            "feedback": "parse_error",
        }


def evaluate_answer(question: str, answer: str, chunks: list[dict]) -> dict:
    """
    Score the answer using the LLM as a judge.

    Args:
        question: The student's original question.
        answer:   The LLM-generated answer to evaluate.
        chunks:   List of chunk dicts with keys: text, source_file, page, chunk_index.

    Returns:
        {
            "score": float,        # 0.0 – 10.0, average of the three criteria
            "relevance": float,
            "accuracy": float,
            "completeness": float,
            "feedback": str,
        }
    """
    context = "\n\n".join(chunk.get("text", "") for chunk in chunks)
    prompt = EVAL_PROMPT.format(
        question=question,
        context=context,
        answer=answer,
    )
    raw = llm.invoke(prompt)
    scores = _parse_scores(raw)
    scores["score"] = round(
        (scores["relevance"] + scores["accuracy"] + scores["completeness"]) / 3, 2
    )
    return scores
