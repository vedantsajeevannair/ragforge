"""Embedder backed by any OpenAI-compatible /embeddings endpoint (OpenAI, Ollama, vLLM...)."""

from __future__ import annotations

import httpx
import numpy as np

from app.embeddings.base import Embedder, l2_normalize


class HTTPEmbedder(Embedder):
    name = "http"

    def __init__(self, base_url: str, model: str, dim: int, api_key: str = "",
                 batch_size: int = 64, timeout: float = 60.0,
                 client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dim = dim
        self.batch_size = batch_size
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = client or httpx.Client(timeout=timeout, headers=headers)

    def _batch(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.post(f"{self.base_url}/embeddings",
                                json={"model": self.model, "input": texts})
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        rows: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            rows.extend(self._batch(texts[i:i + self.batch_size]))
        matrix = np.asarray(rows, dtype=np.float32)
        if matrix.shape[1] != self.dim:
            raise ValueError(f"expected dim {self.dim}, endpoint returned {matrix.shape[1]}")
        return l2_normalize(matrix)
