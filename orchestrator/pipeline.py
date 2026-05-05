# orchestrator/pipeline.py
# ─────────────────────────────────────────────────────────────
# Responsibility: Tie all four agents together into a single
# callable pipeline with retry logic.
#
# The UI (app.py) calls run_pipeline(question) and receives a
# complete result dict — it never imports agents directly.
#
# Retry logic:
#   1. Retrieve chunks → generate answer → monitor → evaluate.
#   2. If monitor flags safety issues, regenerate immediately.
#   3. If evaluator score < SCORE_THRESHOLD, regenerate (max
#      MAX_RETRIES times). After retries exhausted, return the
#      best answer we have.
# ─────────────────────────────────────────────────────────────

from agents.retrieval_agent import retrieve
from agents.answer_agent import generate_answer
from agents.monitor_agent import check_answer
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
