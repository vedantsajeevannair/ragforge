"""Query preprocessing: normalisation and simple expansion."""

from __future__ import annotations

import re

_QUESTION_PREFIX = re.compile(
    r"^(please\s+)?(can you\s+|could you\s+)?(tell me|explain|describe)\s+", re.IGNORECASE
)

DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "rag": ["retrieval augmented generation"],
    "llm": ["large language model"],
    "bm25": ["lexical ranking"],
    "db": ["database"],
    "ml": ["machine learning"],
}


def normalize_query(query: str) -> str:
    query = " ".join(query.split())
    query = _QUESTION_PREFIX.sub("", query)
    return query.rstrip("?!. ").strip()


def expand_query(query: str, synonyms: dict[str, list[str]] | None = None) -> str:
    synonyms = DEFAULT_SYNONYMS if synonyms is None else synonyms
    extra = []
    for word in re.findall(r"\w+", query.lower()):
        extra.extend(synonyms.get(word, []))
    return f"{query} {' '.join(extra)}".strip() if extra else query
