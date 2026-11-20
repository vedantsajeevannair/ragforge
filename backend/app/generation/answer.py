"""The RAG answer pipeline: retrieve, build prompt, generate, attach citations."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.generation.citations import Citation, resolve_citations, strip_invalid_markers
from app.generation.confidence import answer_confidence
from app.generation.extractive import NOT_FOUND
from app.generation.prompt import SYSTEM_PROMPT, build_user_prompt
from app.generation.providers import LLMProvider
from app.vectorstore.base import SearchHit


@dataclass
class Answer:
    question: str
    answer: str
    citations: list[Citation]
    hits: list[SearchHit]
    timings_ms: dict[str, float] = field(default_factory=dict)
    grounded: bool = True
    confidence: float = 0.0


class AnswerEngine:
    def __init__(self, kb: KnowledgeBase, llm: LLMProvider, min_score: float = 0.0,
                 max_context_chars: int = 12000, system_prompt: str = "") -> None:
        self.kb = kb
        self.llm = llm
        self.min_score = min_score
        self.max_context_chars = max_context_chars
        self.system_prompt = system_prompt or SYSTEM_PROMPT

    def answer(self, question: str, options: SearchOptions | None = None) -> Answer:
        t0 = time.perf_counter()
        hits = [h for h in self.kb.search(question, options) if h.score >= self.min_score]
        t1 = time.perf_counter()
        if not hits:
            return Answer(question, NOT_FOUND, [], [],
                          {"retrieval": (t1 - t0) * 1000, "generation": 0.0}, grounded=False)
        user = build_user_prompt(question, hits, self.max_context_chars)
        raw = self.llm.complete(self.system_prompt, user)
        t2 = time.perf_counter()
        text = strip_invalid_markers(raw, len(hits)).strip()
        citations = resolve_citations(text, hits)
        return Answer(
            question=question,
            answer=text,
            citations=citations,
            hits=hits,
            timings_ms={"retrieval": (t1 - t0) * 1000, "generation": (t2 - t1) * 1000},
            grounded=bool(citations),
            confidence=answer_confidence(question, text, hits, citations),
        )

    def stream(self, question: str, options: SearchOptions | None = None) -> Iterator[dict]:
        """Yield events: one 'sources', many 'token', then one 'done' with citations."""
        t0 = time.perf_counter()
        hits = [h for h in self.kb.search(question, options) if h.score >= self.min_score]
        t1 = time.perf_counter()
        yield {"type": "sources", "hits": hits}
        if not hits:
            yield {"type": "token", "text": NOT_FOUND}
            yield {"type": "done", "answer": NOT_FOUND, "citations": [], "grounded": False,
                   "confidence": 0.0,
                   "timings_ms": {"retrieval": (t1 - t0) * 1000, "generation": 0.0}}
            return
        user = build_user_prompt(question, hits, self.max_context_chars)
        parts = []
        for token in self.llm.stream(self.system_prompt, user):
            parts.append(token)
            yield {"type": "token", "text": token}
        t2 = time.perf_counter()
        text = strip_invalid_markers("".join(parts), len(hits)).strip()
        citations = resolve_citations(text, hits)
        yield {"type": "done", "answer": text, "citations": citations,
               "grounded": bool(citations),
               "confidence": answer_confidence(question, text, hits, citations),
               "timings_ms": {"retrieval": (t1 - t0) * 1000, "generation": (t2 - t1) * 1000}}
