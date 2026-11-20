"""A rough 0-1 confidence for an answer, shown so users know when to double-check.

Combines how well the best passage covers the question with how much of the answer is
backed by citations. It is a heuristic, not a calibrated probability.
"""

from __future__ import annotations

import re

from app.generation.citations import Citation
from app.retrieval.rerank import term_coverage
from app.vectorstore.base import SearchHit

_SENTENCE = re.compile(r"[^.!?]+[.!?]*")
_MARKER = re.compile(r"\[\d{1,3}\]")


def cited_sentence_ratio(answer: str) -> float:
    sentences = [s for s in _SENTENCE.findall(answer) if s.strip(" []0123456789")]
    if not sentences:
        return 0.0
    return sum(1 for s in sentences if _MARKER.search(s)) / len(sentences)


def answer_confidence(question: str, answer: str, hits: list[SearchHit],
                      citations: list[Citation]) -> float:
    if not hits or not citations:
        return 0.0
    coverage = max(term_coverage(question, h.chunk.text) for h in hits)
    return round(0.6 * coverage + 0.4 * cited_sentence_ratio(answer), 3)


def confidence_label(score: float) -> str:
    return "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
