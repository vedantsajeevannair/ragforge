"""Lightweight re-ranker combining first-stage score with query-term coverage.

A cross-encoder would be stronger, but this keeps the default install model-free.
"""

from __future__ import annotations

from app.text.tokenize import terms
from app.vectorstore.base import SearchHit


def term_coverage(query: str, text: str) -> float:
    q = set(terms(query))
    if not q:
        return 0.0
    return len(q & set(terms(text))) / len(q)


def phrase_bonus(query: str, text: str) -> float:
    """1.0 if any 2-word query phrase appears verbatim in the text."""
    words = query.lower().split()
    lowered = text.lower()
    pairs = (" ".join(words[i:i + 2]) for i in range(len(words) - 1))
    return 1.0 if any(p in lowered for p in pairs) else 0.0


def rerank(query: str, hits: list[SearchHit], alpha: float = 0.5,
           phrase_weight: float = 0.1) -> list[SearchHit]:
    if not hits:
        return []
    top = max(h.score for h in hits) or 1.0
    rescored = []
    for h in hits:
        score = ((1 - alpha) * h.score / top
                 + alpha * term_coverage(query, h.chunk.text)
                 + phrase_weight * phrase_bonus(query, h.chunk.text))
        rescored.append(SearchHit(h.chunk, score))
    return sorted(rescored, key=lambda h: -h.score)
