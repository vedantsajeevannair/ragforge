"""Offline answerer: picks the context sentences that best match the question.

Used when no LLM is configured. It never invents text, so every sentence is
traceable to a passage and carries its citation.
"""

from __future__ import annotations

import re

from app.generation.providers import LLMProvider
from app.ingestion.chunking import split_sentences
from app.retrieval.followup import content_terms
from app.text.tokenize import stem, terms

_HEADING_LINE = re.compile(r"^\s{0,3}#{1,6}\s+.*$", re.MULTILINE)
_BLOCK = re.compile(r"^\[(\d+)\] Source: [^\n]*\n(.*?)(?=\n\n\[\d+\] Source: |\Z)",
                    re.MULTILINE | re.DOTALL)
NOT_FOUND = "I could not find an answer to that in the documents."


def _strip_headings(text: str) -> str:
    """Drop Markdown heading lines so they are not glued onto the next sentence."""
    return _HEADING_LINE.sub("", text)


def _parse_prompt(user: str) -> tuple[list[tuple[int, str]], str]:
    context, _, question = user.rpartition("\n\nQuestion: ")
    blocks = [(int(m.group(1)), m.group(2).strip()) for m in _BLOCK.finditer(context)]
    return blocks, question.strip()


class ExtractiveProvider(LLMProvider):
    name = "extractive"

    def __init__(self, max_sentences: int = 3, min_overlap: float = 0.2,
                 relative_cutoff: float = 0.6) -> None:
        self.max_sentences = max_sentences
        self.min_overlap = min_overlap
        # Only keep sentences scoring at least this share of the best sentence, so a
        # strong match is not padded with loosely related filler.
        self.relative_cutoff = relative_cutoff

    def complete(self, system: str, user: str) -> str:
        blocks, question = _parse_prompt(user)
        # Question words ("how", "does") would otherwise reward any sentence containing them.
        q_terms = {stem(t) for t in content_terms(question)}
        if not q_terms:
            return NOT_FOUND
        scored = []
        for rank, (num, text) in enumerate(blocks):
            text = _strip_headings(text)
            for s, e in split_sentences(text):
                sentence = " ".join(text[s:e].split())
                s_terms = set(terms(sentence))
                if not s_terms:
                    continue
                overlap = len(q_terms & s_terms) / len(q_terms)
                if overlap >= self.min_overlap:
                    # small penalty for lower-ranked passages keeps ties in retrieval order
                    scored.append((overlap - 0.01 * rank, num, sentence))
        if not scored:
            return NOT_FOUND
        scored.sort(key=lambda x: -x[0])
        floor = scored[0][0] * self.relative_cutoff
        picked, seen = [], set()
        for score, num, sentence in scored:
            if score < floor:
                break
            if sentence.lower() in seen:
                continue
            seen.add(sentence.lower())
            picked.append(f"{sentence.rstrip()} [{num}]")
            if len(picked) == self.max_sentences:
                break
        return " ".join(picked)
