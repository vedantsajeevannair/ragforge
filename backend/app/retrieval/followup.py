"""Turn a follow-up question into a standalone search query.

"What about its parameters?" after "How does BM25 work?" should search for BM25
parameters. Without an LLM, we detect follow-ups by pronouns/short length and carry
over the content terms of the previous question.
"""

from __future__ import annotations

import re

from app.text.tokenize import STOPWORDS, tokenize

_FOLLOWUP_CUES = re.compile(
    r"\b(it|its|this|that|these|those|they|them|their|he|she|one|ones)\b"
    r"|^(and|what about|how about|why|also)\b",
    re.IGNORECASE,
)
_QUESTION_WORDS = {"what", "how", "why", "when", "where", "which", "who", "does", "do", "can",
                   "about", "also", "explain", "tell", "work", "works", "mean", "means"}


def is_followup(question: str) -> bool:
    words = tokenize(question)
    return bool(_FOLLOWUP_CUES.search(question.strip())) or len(words) <= 3


def content_terms(text: str) -> list[str]:
    return [w for w in tokenize(text) if w not in STOPWORDS and w not in _QUESTION_WORDS]


def condense_question(question: str, previous: list[str], max_carry: int = 6) -> str:
    """Append key terms from the most recent previous question when needed."""
    if not previous or not is_followup(question):
        return question
    own = set(content_terms(question))
    carry = [t for t in dict.fromkeys(content_terms(previous[-1])) if t not in own]
    if not carry:
        return question
    return f"{question.strip()} ({' '.join(carry[:max_carry])})"
