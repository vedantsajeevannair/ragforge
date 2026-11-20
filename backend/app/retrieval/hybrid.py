"""Hybrid retrieval using Reciprocal Rank Fusion (Cormack et al., 2009)."""

from __future__ import annotations

from app.retrieval.base import Retriever
from app.vectorstore.base import MetadataFilter, SearchHit


def reciprocal_rank_fusion(
    rankings: list[list[SearchHit]], k: int = 60, weights: list[float] | None = None
) -> list[SearchHit]:
    """Fuse ranked lists; score(d) = sum_i w_i / (k + rank_i(d))."""
    weights = weights or [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("one weight per ranking is required")
    fused: dict[str, float] = {}
    chunks = {}
    for ranking, weight in zip(rankings, weights, strict=True):
        for rank, hit in enumerate(ranking, start=1):
            cid = hit.chunk.chunk_id
            fused[cid] = fused.get(cid, 0.0) + weight / (k + rank)
            chunks.setdefault(cid, hit.chunk)
    order = sorted(fused, key=lambda cid: -fused[cid])
    return [SearchHit(chunks[cid], fused[cid]) for cid in order]


class HybridRetriever(Retriever):
    name = "hybrid"

    def __init__(self, retrievers: list[Retriever], weights: list[float] | None = None,
                 candidate_multiplier: int = 4, rrf_k: int = 60) -> None:
        if not retrievers:
            raise ValueError("at least one retriever is required")
        self.retrievers = retrievers
        self.weights = weights
        self.candidate_multiplier = candidate_multiplier
        self.rrf_k = rrf_k

    def retrieve(self, query: str, k: int, flt: MetadataFilter | None = None) -> list[SearchHit]:
        pool = max(k * self.candidate_multiplier, k)
        rankings = [r.retrieve(query, pool, flt) for r in self.retrievers]
        return reciprocal_rank_fusion(rankings, self.rrf_k, self.weights)[:k]
