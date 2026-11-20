"""Offline embedder based on the hashing trick.

Each text becomes a sparse bag of word terms and character n-grams, hashed into a
fixed number of buckets with a sign hash to reduce collision bias. Sub-linear term
frequency keeps long chunks from dominating. Needs no model download, so the app
works offline and tests are deterministic.
"""

from __future__ import annotations

import hashlib

import numpy as np

from app.embeddings.base import Embedder, l2_normalize
from app.text.tokenize import terms


def _hash(feature: str) -> int:
    return int.from_bytes(hashlib.blake2b(feature.encode(), digest_size=8).digest(), "little")


class HashingEmbedder(Embedder):
    name = "hashing"

    def __init__(self, dim: int = 512, ngram_range: tuple[int, int] = (3, 4),
                 char_weight: float = 0.5) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim
        self.ngram_range = ngram_range
        self.char_weight = char_weight

    def _features(self, text: str) -> dict[str, float]:
        feats: dict[str, float] = {}
        words = terms(text)
        for w in words:
            feats["w:" + w] = feats.get("w:" + w, 0.0) + 1.0
        lo, hi = self.ngram_range
        for w in words:
            padded = f"<{w}>"
            for n in range(lo, hi + 1):
                for i in range(len(padded) - n + 1):
                    key = "c:" + padded[i:i + n]
                    feats[key] = feats.get(key, 0.0) + self.char_weight
        return feats

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for feat, count in self._features(text).items():
                h = _hash(feat)
                sign = 1.0 if (h >> 63) & 1 else -1.0
                out[row, h % self.dim] += sign * (1.0 + np.log(count))
        return l2_normalize(out)
