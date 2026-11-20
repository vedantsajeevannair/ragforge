"""Okapi BM25 index over stored chunks."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable

from app.text.tokenize import terms
from app.vectorstore.base import MetadataFilter, SearchHit, StoredChunk, matches


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75,
                 text_fn: Callable[[StoredChunk], str] | None = None) -> None:
        self.k1 = k1
        self.b = b
        self.text_fn = text_fn or (lambda c: c.text)
        self._chunks: list[StoredChunk] = []
        self._tfs: list[Counter[str]] = []
        self._lengths: list[int] = []
        self._df: Counter[str] = Counter()

    def __len__(self) -> int:
        return len(self._chunks)

    @property
    def avg_length(self) -> float:
        return sum(self._lengths) / len(self._lengths) if self._lengths else 0.0

    def add(self, chunks: list[StoredChunk]) -> None:
        for chunk in chunks:
            tf = Counter(terms(self.text_fn(chunk)))
            self._chunks.append(chunk)
            self._tfs.append(tf)
            self._lengths.append(sum(tf.values()))
            self._df.update(tf.keys())

    def rebuild(self, chunks: list[StoredChunk]) -> None:
        self.__init__(self.k1, self.b, self.text_fn)
        self.add(chunks)

    def idf(self, term: str) -> float:
        n, df = len(self._chunks), self._df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> list[float]:
        q_terms = terms(query)
        avg = self.avg_length or 1.0
        scores = [0.0] * len(self._chunks)
        for term in set(q_terms):
            idf = self.idf(term)
            for i, tf in enumerate(self._tfs):
                f = tf.get(term)
                if not f:
                    continue
                norm = self.k1 * (1 - self.b + self.b * self._lengths[i] / avg)
                scores[i] += idf * f * (self.k1 + 1) / (f + norm)
        return scores

    def search(self, query: str, k: int, flt: MetadataFilter | None = None) -> list[SearchHit]:
        scored = [
            (s, i) for i, s in enumerate(self.score(query))
            if s > 0 and matches(self._chunks[i].metadata, flt)
        ]
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [SearchHit(self._chunks[i], s) for s, i in scored[:k]]
