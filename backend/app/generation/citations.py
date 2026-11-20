"""Parse [n] citation markers out of model output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.generation.prompt import source_label
from app.vectorstore.base import SearchHit

_MARKER = re.compile(r"\[(\d{1,3})\]")


@dataclass
class Citation:
    number: int
    chunk_id: str
    doc_id: str
    source: str
    snippet: str


def cited_numbers(answer: str) -> list[int]:
    seen: list[int] = []
    for m in _MARKER.finditer(answer):
        n = int(m.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def resolve_citations(answer: str, hits: list[SearchHit],
                      snippet_chars: int = 240) -> list[Citation]:
    """Map markers to hits; markers that point past the context are ignored."""
    out = []
    for n in cited_numbers(answer):
        if 1 <= n <= len(hits):
            hit = hits[n - 1]
            text = hit.chunk.text.strip()
            snippet = text if len(text) <= snippet_chars else text[:snippet_chars].rstrip() + "…"
            out.append(Citation(n, hit.chunk.chunk_id, hit.chunk.doc_id, source_label(hit),
                                snippet))
    return out


def strip_invalid_markers(answer: str, n_hits: int) -> str:
    return _MARKER.sub(lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_hits else "", answer)
