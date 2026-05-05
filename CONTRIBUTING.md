# Contributing to EduAgent

## Branch Strategy

- `main` — production-ready only. Never push directly.
- `develop` — integration branch. All feature branches merge here.

Always branch from `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Pull Requests

- Open PRs against `develop`, not `main`.
- Every PR requires **1 reviewer approval** before merging.
- Include a short description of what changed and why.

## Before Opening a PR

Run the full test suite and make sure it passes:

```bash
pytest tests/ -v
```

If you added new code, consider running with coverage:

```bash
pytest tests/ -v --cov=agents --cov=rag --cov=orchestrator --cov-report=term-missing
```

## Code Style

- Follow PEP 8.
- Keep functions small and focused.
- Do not change shared data contracts (agent signatures) without team discussion.

---

*EduAgent — 7-Person Team*
