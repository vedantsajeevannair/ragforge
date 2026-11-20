"""The RAG answer pipeline: retrieve, build prompt, generate, attach citations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.generation.citations import Citation, resolve_citations, strip_invalid_markers
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


class AnswerEngine:
    def __init__(self, kb: KnowledgeBase, llm: LLMProvider, min_score: float = 0.0,
                 max_context_chars: int = 12000) -> None:
        self.kb = kb
        self.llm = llm
        self.min_score = min_score
        self.max_context_chars = max_context_chars

    def answer(self, question: str, options: SearchOptions | None = None) -> Answer:
        t0 = time.perf_counter()
        hits = [h for h in self.kb.search(question, options) if h.score >= self.min_score]
        t1 = time.perf_counter()
        if not hits:
            return Answer(question, NOT_FOUND, [], [],
                          {"retrieval": (t1 - t0) * 1000, "generation": 0.0}, grounded=False)
        user = build_user_prompt(question, hits, self.max_context_chars)
        raw = self.llm.complete(SYSTEM_PROMPT, user)
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
        )
