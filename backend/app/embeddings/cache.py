"""LRU cache wrapper so repeated queries are not re-embedded."""

from __future__ import annotations

from collections import OrderedDict

import numpy as np

from app.embeddings.base import Embedder


class CachedEmbedder(Embedder):
    def __init__(self, inner: Embedder, max_items: int = 2048) -> None:
        self.inner = inner
        self.name = f"cached-{inner.name}"
        self.dim = inner.dim
        self.max_items = max_items
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def embed(self, texts: list[str]) -> np.ndarray:
        missing = [t for t in dict.fromkeys(texts) if t not in self._cache]
        self.misses += len(missing)
        self.hits += len(texts) - len(missing)
        if missing:
            for text, vec in zip(missing, self.inner.embed(missing), strict=True):
                self._cache[text] = vec
                if len(self._cache) > self.max_items:
                    self._cache.popitem(last=False)
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            vec = self._cache.get(text)
            if vec is None:  # evicted within this call
                vec = self.inner.embed_one(text)
            else:
                self._cache.move_to_end(text)
            out[i] = vec
        return out
