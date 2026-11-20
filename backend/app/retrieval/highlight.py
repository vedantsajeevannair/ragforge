"""Find spans of query terms inside a passage, for highlighting in the UI."""

from __future__ import annotations

import re

from app.text.tokenize import STOPWORDS, stem, tokenize

_WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")


def highlight_spans(query: str, text: str, max_spans: int = 50) -> list[tuple[int, int]]:
    """(start, end) offsets of words in `text` whose stem matches a query term."""
    wanted = {stem(t) for t in tokenize(query) if t not in STOPWORDS}
    if not wanted:
        return []
    spans: list[tuple[int, int]] = []
    for m in _WORD.finditer(text):
        if stem(m.group(0).lower()) in wanted:
            spans.append((m.start(), m.end()))
            if len(spans) >= max_spans:
                break
    return spans
