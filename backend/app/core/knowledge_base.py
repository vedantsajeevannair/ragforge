"""KnowledgeBase: one place that owns the embedder, vector store and BM25 index."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Literal

from app.embeddings.base import Embedder
from app.ingestion.pipeline import IngestResult
from app.retrieval.bm25 import BM25Index
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.mmr import mmr_rerank
from app.retrieval.query import expand_query, normalize_query
from app.retrieval.rerank import rerank
from app.vectorstore.base import MetadataFilter, SearchHit, StoredChunk, VectorStore

SearchMode = Literal["dense", "bm25", "hybrid"]


@dataclass
class SearchOptions:
    k: int = 5
    mode: SearchMode = "hybrid"
    flt: MetadataFilter | None = None
    use_mmr: bool = False
    mmr_lambda: float = 0.7
    use_rerank: bool = True
    expand: bool = True


def chunk_header(metadata: dict) -> str:
    """Short context line: file stem plus heading path, e.g. 'bm25 > BM25 > Parameters'."""
    source = str(metadata.get("source", ""))
    stem = source.rsplit(".", 1)[0].replace("-", " ").replace("_", " ")
    parts = [p for p in (stem, metadata.get("title"), metadata.get("section")) if p]
    return " > ".join(dict.fromkeys(parts))


class KnowledgeBase:
    def __init__(self, embedder: Embedder, store: VectorStore,
                 contextual_headers: bool = False) -> None:
        self.embedder = embedder
        self.store = store
        # Index each chunk together with its file/section header so short chunks keep
        # the topic they belong to ("Parameters" alone says little; "BM25 > Parameters"
        # does). The stored text shown to users stays unchanged. Off by default: on the
        # sample benchmark it lowered BM25 hit@1 from 0.923 to 0.885 and did not help
        # the other configurations (see docs/evaluation.md).
        self.contextual_headers = contextual_headers
        self.bm25 = BM25Index(text_fn=self._index_text)
        self.bm25.add(store.all_chunks())
        self._lock = threading.RLock()
        self._retrievers = {
            "dense": DenseRetriever(embedder, store),
            "bm25": LexicalRetriever(self.bm25),
        }
        self._retrievers["hybrid"] = HybridRetriever(
            [self._retrievers["dense"], self._retrievers["bm25"]]
        )

    def add(self, result: IngestResult, collection: str = "default") -> list[StoredChunk]:
        doc = result.document
        stored = [
            StoredChunk(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                text=c.text,
                metadata={**c.metadata, "source": doc.source, "collection": collection,
                          "start": c.start, "end": c.end},
            )
            for c in result.chunks
        ]
        if not stored:
            return []
        vectors = self.embedder.embed([self._index_text(s) for s in stored])
        with self._lock:
            self.store.delete_document(doc.doc_id)
            self.store.add(stored, vectors)
            self.bm25.rebuild(self.store.all_chunks())
        return stored

    def _index_text(self, chunk: StoredChunk) -> str:
        if not self.contextual_headers:
            return chunk.text
        header = chunk_header(chunk.metadata)
        return f"{header}\n{chunk.text}" if header else chunk.text

    def delete(self, doc_id: str) -> int:
        with self._lock:
            removed = self.store.delete_document(doc_id)
            if removed:
                self.bm25.rebuild(self.store.all_chunks())
            return removed

    def search(self, query: str, options: SearchOptions | None = None) -> list[SearchHit]:
        opts = options or SearchOptions()
        q = normalize_query(query)
        if not q:
            return []
        q_search = expand_query(q) if opts.expand else q
        pool = opts.k * 3 if (opts.use_mmr or opts.use_rerank) else opts.k
        with self._lock:
            hits = self._retrievers[opts.mode].retrieve(q_search, pool, opts.flt)
        if opts.use_rerank:
            hits = rerank(q, hits)
        if opts.use_mmr:
            hits = mmr_rerank(q, hits, self.embedder, opts.k, opts.mmr_lambda)
        return hits[: opts.k]

    def stats(self) -> dict[str, int]:
        chunks = self.store.all_chunks()
        return {"chunks": len(chunks), "documents": len({c.doc_id for c in chunks})}
