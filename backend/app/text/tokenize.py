"""Lightweight tokenisation shared by lexical search and hashing embeddings."""

import re

_TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

STOPWORDS = frozenset(
    """a an and are as at be but by for from has have he her his i if in into is it its
    me my no not of on or our she so that the their them then there these they this to
    was we were what when where which who will with you your""".split()
)


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def stem(token: str) -> str:
    """Tiny suffix stripper: good enough to match plural and -ing/-ed forms."""
    for suffix in ("ingly", "edly", "ing", "ies", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            if suffix == "ies":
                return token[: -len(suffix)] + "y"
            if suffix == "es" and not token.endswith(("ses", "xes", "zes", "ches", "shes")):
                return token[:-1]
            return token[: -len(suffix)]
    return token


def terms(text: str, remove_stopwords: bool = True) -> list[str]:
    tokens = tokenize(text)
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    return [stem(t) for t in tokens]
