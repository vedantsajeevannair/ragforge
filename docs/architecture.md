# Architecture

## Request flow for a question

1. **`POST /ask/stream`** receives the question, mode, k, an optional collection and up to ten
   previous questions.
2. **Follow-up condensing** (`retrieval/followup.py`): if the question looks like a follow-up
   ("what about its parameters?"), content words from the previous question are appended.
3. **Query normalisation** (`retrieval/query.py`) strips filler such as "can you explain" and
   adds synonyms for common abbreviations (RAG, LLM, BM25).
4. **Retrieval** (`core/knowledge_base.py`): the chosen retriever returns `3 × k` candidates.
   - `dense`: embed the query, cosine similarity over the vector store.
   - `bm25`: Okapi BM25 over the same chunks.
   - `hybrid`: both, merged with weighted reciprocal rank fusion.
5. **Re-ranking** (`retrieval/rerank.py`): blends the first-stage score with query-term coverage
   and an exact-phrase bonus. Optional **MMR** (`retrieval/mmr.py`) then removes near-duplicates.
6. **Prompting** (`generation/prompt.py`): the top k passages become numbered blocks with their
   source, page and section, capped at a character budget.
7. **Generation** (`generation/providers.py`, `generation/extractive.py`): tokens stream from the
   configured provider.
8. **Citations** (`generation/citations.py`): `[n]` markers outside the passage range are removed;
   the rest are resolved to snippets. An answer with no valid citation is marked not grounded.
9. The answer, citations and timings are written to the `queries` table for history and stats.

## Ingestion

```
bytes ─▶ loader (pdf/docx/md/html/txt/csv/json) ─▶ clean_text ─▶ chunker ─▶ page mapping
      ─▶ KnowledgeBase.add: embed + upsert into vector store + rebuild BM25
      ─▶ documents table + original file in data/files/<doc_id>
```

Document ids are a hash of file name and content, so uploading the same file again replaces its
chunks instead of duplicating them.

## Storage

| What | Where |
|---|---|
| Users, documents, query history | SQLite `data/ragforge.db`, versioned migrations |
| Chunk text and metadata | `data/index/chunks.jsonl` |
| Embeddings | `data/index/vectors.npy` (written atomically) |
| Original uploads | `data/files/<doc_id>` |
| JWT secret (if not configured) | `data/.jwt_secret`, mode 600 |

The vector store is brute force (one matrix multiply). That is fast up to a few hundred thousand
chunks; beyond that, swap `PersistentVectorStore` for an ANN index behind the same `VectorStore`
interface.

## Concurrency

`KnowledgeBase` guards index updates and searches with a re-entrant lock, so uploads and
questions from several users do not see a half-rebuilt BM25 index. SQLite access goes through a
single connection protected by a lock.

## Extending

- **New file type**: write `load_x(data, source) -> Document` and call `register_loader(".x", load_x)`.
- **New embedding model**: subclass `Embedder` or point `RAGFORGE_EMBEDDING_PROVIDER=http` at any
  OpenAI-compatible endpoint.
- **New LLM**: subclass `LLMProvider` with `complete` and optionally `stream`.
