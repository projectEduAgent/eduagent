# scripts/smoke_test.py
# ─────────────────────────────────────────────────────────────
# End-to-end smoke test for the EduAgent pipeline.
# Run after all agents are merged into develop.
#
# Usage:
#   python scripts/smoke_test.py
# ─────────────────────────────────────────────────────────────

import os
from rag.pipeline import load_and_index_pdf
from orchestrator.pipeline import run_pipeline

SAMPLE_PDF = "data/sample.pdf"


def main() -> None:
    if not os.path.exists(SAMPLE_PDF):
        print(f"SKIP: No sample PDF found at {SAMPLE_PDF}")
        return

    print("Indexing sample PDF...")
    load_and_index_pdf(SAMPLE_PDF)

    print("Running pipeline...")
    result = run_pipeline("What is the main topic of this document?")

    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    assert result["score"] > 0, "Expected a positive score"
    assert result["answer"], "Expected a non-empty answer"
    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
