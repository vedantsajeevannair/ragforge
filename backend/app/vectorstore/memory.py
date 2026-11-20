"""Brute-force in-memory store using a single numpy matrix (cosine similarity)."""

from __future__ import annotations

import numpy as np

from app.vectorstore.base import MetadataFilter, SearchHit, StoredChunk, VectorStore, matches


class InMemoryVectorStore(VectorStore):
    def __init__(self, dim: int) -> None:
        self.dim = dim
        self._chunks: list[StoredChunk] = []
        self._matrix = np.zeros((0, dim), dtype=np.float32)
        self._index: dict[str, int] = {}

    def add(self, chunks: list[StoredChunk], vectors: np.ndarray) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        if len(vectors) and vectors.shape[1] != self.dim:
            raise ValueError(f"expected dim {self.dim}, got {vectors.shape[1]}")
        fresh_rows, fresh_chunks = [], []
        for chunk, vec in zip(chunks, vectors, strict=True):
            if chunk.chunk_id in self._index:  # upsert
                i = self._index[chunk.chunk_id]
                self._chunks[i] = chunk
                self._matrix[i] = vec
            else:
                self._index[chunk.chunk_id] = len(self._chunks) + len(fresh_chunks)
                fresh_chunks.append(chunk)
                fresh_rows.append(vec)
        if fresh_chunks:
            self._chunks.extend(fresh_chunks)
            self._matrix = np.vstack([self._matrix, np.asarray(fresh_rows, dtype=np.float32)])

    def search(self, vector: np.ndarray, k: int,
               flt: MetadataFilter | None = None) -> list[SearchHit]:
        if not self._chunks or k <= 0:
            return []
        scores = self._matrix @ vector.astype(np.float32)
        if flt:
            mask = np.array([matches(c.metadata, flt) for c in self._chunks])
            scores = np.where(mask, scores, -np.inf)
        k = min(k, len(self._chunks))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [SearchHit(self._chunks[i], float(scores[i])) for i in top
                if np.isfinite(scores[i])]

    def delete_document(self, doc_id: str) -> int:
        keep = [i for i, c in enumerate(self._chunks) if c.doc_id != doc_id]
        removed = len(self._chunks) - len(keep)
        if removed:
            self._chunks = [self._chunks[i] for i in keep]
            self._matrix = self._matrix[keep]
            self._index = {c.chunk_id: i for i, c in enumerate(self._chunks)}
        return removed

    def all_chunks(self) -> list[StoredChunk]:
        return list(self._chunks)
