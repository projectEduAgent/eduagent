#!/usr/bin/env bash
# scripts/run_tests.sh
# ─────────────────────────────────────────────────────────────
# Run the full EduAgent test suite with coverage reporting.
#
# Usage:
#   bash scripts/run_tests.sh
#   bash scripts/run_tests.sh --html   # generates htmlcov/
# ─────────────────────────────────────────────────────────────

set -euo pipefail

COVERAGE_ARGS=(
    --cov=agents
    --cov=rag
    --cov=orchestrator
    --cov-report=term-missing
)

if [[ "${1:-}" == "--html" ]]; then
    COVERAGE_ARGS+=(--cov-report=html)
    echo "HTML coverage report will be generated at htmlcov/index.html"
fi

echo "Running pytest..."
pytest tests/ -v "${COVERAGE_ARGS[@]}"
