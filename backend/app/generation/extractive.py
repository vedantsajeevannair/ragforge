"""Offline answerer: picks the context sentences that best match the question.

Used when no LLM is configured. It never invents text, so every sentence is
traceable to a passage and carries its citation.
"""

from __future__ import annotations

import re

from app.generation.providers import LLMProvider
from app.ingestion.chunking import split_sentences
from app.text.tokenize import terms

_BLOCK = re.compile(r"^\[(\d+)\] Source: [^\n]*\n(.*?)(?=\n\n\[\d+\] Source: |\Z)",
                    re.MULTILINE | re.DOTALL)
NOT_FOUND = "I could not find an answer to that in the documents."


def _parse_prompt(user: str) -> tuple[list[tuple[int, str]], str]:
    context, _, question = user.rpartition("\n\nQuestion: ")
    blocks = [(int(m.group(1)), m.group(2).strip()) for m in _BLOCK.finditer(context)]
    return blocks, question.strip()


class ExtractiveProvider(LLMProvider):
    name = "extractive"

    def __init__(self, max_sentences: int = 3, min_overlap: float = 0.2) -> None:
        self.max_sentences = max_sentences
        self.min_overlap = min_overlap

    def complete(self, system: str, user: str) -> str:
        blocks, question = _parse_prompt(user)
        q_terms = set(terms(question))
        if not q_terms:
            return NOT_FOUND
        scored = []
        for rank, (num, text) in enumerate(blocks):
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
        picked, seen = [], set()
        for _, num, sentence in scored:
            if sentence.lower() in seen:
                continue
            seen.add(sentence.lower())
            picked.append(f"{sentence.rstrip()} [{num}]")
            if len(picked) == self.max_sentences:
                break
        return " ".join(picked)
