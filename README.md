# RAGForge

[![CI](https://github.com/vedantsajeevannair/ragforge/actions/workflows/ci.yml/badge.svg)](https://github.com/vedantsajeevannair/ragforge/actions/workflows/ci.yml)

Retrieval-augmented question answering over your own documents. Upload PDFs, Markdown, HTML or
plain text, ask questions, and get answers that cite the passages they came from.

It runs fully offline by default (hashing embeddings plus an extractive answerer) and can be
switched to Claude, any OpenAI-compatible API, or a local Ollama model with one environment variable.

## Features

- **Ingestion**: PDF (with page numbers), Markdown (heading-aware), HTML and text loaders;
  fixed, recursive, sentence and Markdown chunkers with overlap.
- **Hybrid retrieval**: BM25 and dense vector search merged with reciprocal rank fusion,
  then a term-coverage re-ranker and optional MMR diversification.
- **Cited answers**: numbered context, `[n]` citations resolved to source snippets,
  invalid citations removed, and an abstain path when nothing relevant is found.
- **Streaming**: answers stream token by token over server-sent events.
- **Evaluation harness**: recall@k, MRR, nDCG, grounding rate and citation precision on a
  labelled question set, run in CI as a regression guard.
- **Multi-user API**: JWT auth with admin and user roles, collections, per-user history,
  answer feedback and per-user rate limiting.
- **React UI**: ask page, document manager with drag-and-drop upload, history and admin stats.

## Architecture

```
            ┌──────────────┐   SSE / JSON   ┌───────────────────────────────────────────┐
  Browser ─▶│ React (Vite) │ ─────────────▶ │ FastAPI                                   │
            └──────────────┘                │  auth · documents · search · ask · stats  │
                                            │                                           │
                                            │  ingest ─▶ clean ─▶ chunk ─▶ embed        │
                                            │                         │                 │
                                            │            ┌────────────┴───────────┐     │
                                            │            ▼                        ▼     │
                                            │      vector store             BM25 index  │
                                            │            └─────── RRF fusion ─────┘     │
                                            │                       ▼                   │
                                            │            re-rank · MMR · prompt         │
                                            │                       ▼                   │
                                            │       LLM (extractive / Claude / OpenAI)  │
                                            │                       ▼                   │
                                            │            answer + resolved citations    │
                                            └───────────────────────────────────────────┘
                                                     SQLite: users, documents, history
```

## Quick start

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd backend && uvicorn app.main:app --reload     # http://localhost:8000/docs

# Frontend (second terminal)
cd frontend && npm install && npm run dev       # http://localhost:5173
```

The first account you register becomes the admin.

Or run everything with Docker:

```bash
cp .env.example .env
docker compose up --build                       # http://localhost:8080
```

### Command line

```bash
cd backend
python -m app.cli index ../samples/corpus --collection docs
python -m app.cli ask "What value of k is usually used in RRF?"
```

## Using a real LLM

| Provider | Settings |
|---|---|
| Offline (default) | `RAGFORGE_LLM_PROVIDER=extractive` |
| Claude | `RAGFORGE_LLM_PROVIDER=anthropic`, `RAGFORGE_LLM_API_KEY=...` |
| OpenAI | `RAGFORGE_LLM_PROVIDER=openai`, `RAGFORGE_LLM_BASE_URL=https://api.openai.com/v1`, `RAGFORGE_LLM_MODEL=...`, `RAGFORGE_LLM_API_KEY=...` |
| Ollama | `RAGFORGE_LLM_PROVIDER=ollama`, `RAGFORGE_LLM_BASE_URL=http://localhost:11434/v1`, `RAGFORGE_LLM_MODEL=llama3.1` |

Embeddings can likewise use any OpenAI-compatible `/embeddings` endpoint with
`RAGFORGE_EMBEDDING_PROVIDER=http`. Changing the embedding model or dimension requires re-indexing.

## Evaluation

`samples/` holds a 9-document corpus about retrieval and 26 labelled questions.

```bash
cd backend && python -m app.eval.cli --corpus ../samples/corpus --dataset ../samples/eval.jsonl
```

Results with the offline hashing embedder, k = 3:

| config | hit@1 | hit@3 | MRR | nDCG@3 |
|---|---:|---:|---:|---:|
| BM25 | 0.923 | 0.962 | 0.942 | 0.947 |
| Dense (hashing) | 0.846 | 0.962 | 0.904 | 0.919 |
| Hybrid (RRF) | 0.885 | 0.962 | 0.923 | 0.933 |
| Hybrid + re-rank + query expansion | **0.962** | 0.962 | **0.962** | **0.962** |
| Hybrid + re-rank + expansion + MMR | 0.846 | 0.923 | 0.885 | 0.895 |

Extractive answers on the same set: grounding rate 1.00, citation precision 0.89, expected-phrase
recall 0.86.

The corpus is small and on one topic, so these numbers show the relative effect of each stage
rather than real-world accuracy. MMR lowers scores here because each question has a single relevant
document; it helps when several near-duplicate chunks compete for the context window.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Get a bearer token |
| GET | `/auth/me` | Current user |
| POST | `/documents` | Upload a file (`file`, `collection`) |
| GET | `/documents`, `/documents/{id}`, `/documents/{id}/chunks` | Browse documents |
| DELETE | `/documents/{id}` | Delete (owner or admin) |
| POST | `/search` | Ranked passages |
| POST | `/ask` | Answer with citations |
| POST | `/ask/stream` | Same, as server-sent events |
| GET | `/history` · POST `/history/{id}/feedback` | Past questions and ratings |
| GET | `/collections`, `/config`, `/stats` | Metadata (stats is admin-only) |

Full interactive docs at `/docs` when the server is running.

## Development

```bash
cd backend && ruff check app tests && pytest -q
cd frontend && npm run typecheck && npm test
```

## License

MIT
