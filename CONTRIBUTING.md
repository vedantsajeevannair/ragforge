# Contributing

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd frontend && npm install
```

## Before opening a pull request

```bash
make check
```

This runs ruff, the backend tests, the retrieval benchmark, the TypeScript check and the
frontend tests.

If you change chunking, retrieval or prompting, paste the benchmark table from
`make bench` into the pull request so reviewers can see the effect.

## Conventions

- Commit messages follow Conventional Commits (`feat(retrieval): ...`, `fix(api): ...`).
- New modules get tests next to the existing ones in `backend/tests` or as `*.test.tsx`.
- Keep the default install offline: anything that needs a network model must be optional.
