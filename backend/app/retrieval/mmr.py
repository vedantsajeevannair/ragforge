"""Maximal Marginal Relevance re-ranking to reduce near-duplicate context."""

from __future__ import annotations

import numpy as np

from app.embeddings.base import Embedder
from app.vectorstore.base import SearchHit


def mmr(query_vec: np.ndarray, doc_vecs: np.ndarray, k: int, lambda_: float = 0.7) -> list[int]:
    """Pick k indices balancing relevance (lambda) against redundancy (1 - lambda)."""
    if not 0.0 <= lambda_ <= 1.0:
        raise ValueError("lambda_ must be in [0, 1]")
    n = len(doc_vecs)
    if n == 0 or k <= 0:
        return []
    relevance = doc_vecs @ query_vec
    selected: list[int] = []
    candidates = list(range(n))
    while candidates and len(selected) < k:
        if selected:
            redundancy = (doc_vecs[candidates] @ doc_vecs[selected].T).max(axis=1)
        else:
            redundancy = np.zeros(len(candidates))
        scores = lambda_ * relevance[candidates] - (1 - lambda_) * redundancy
        best = candidates[int(np.argmax(scores))]
        selected.append(best)
        candidates.remove(best)
    return selected


def mmr_rerank(query: str, hits: list[SearchHit], embedder: Embedder, k: int,
               lambda_: float = 0.7) -> list[SearchHit]:
    if not hits:
        return []
    vecs = embedder.embed([h.chunk.text for h in hits])
    order = mmr(embedder.embed_one(query), vecs, k, lambda_)
    return [hits[i] for i in order]
