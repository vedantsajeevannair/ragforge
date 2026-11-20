"""Disk-backed store: chunks in JSONL, vectors in a .npy file, saved atomically."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.vectorstore.base import StoredChunk
from app.vectorstore.memory import InMemoryVectorStore


def _atomic_write(path: Path, write) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            write(fh)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class PersistentVectorStore(InMemoryVectorStore):
    def __init__(self, dim: int, directory: str | Path) -> None:
        super().__init__(dim)
        self.directory = Path(directory)
        self._chunks_path = self.directory / "chunks.jsonl"
        self._vectors_path = self.directory / "vectors.npy"
        self.load()

    def load(self) -> None:
        if not (self._chunks_path.exists() and self._vectors_path.exists()):
            return
        with self._chunks_path.open() as fh:
            chunks = [StoredChunk(**json.loads(line)) for line in fh if line.strip()]
        vectors = np.load(self._vectors_path)
        if vectors.shape != (len(chunks), self.dim):
            raise ValueError(
                f"index at {self.directory} has shape {vectors.shape}, "
                f"expected ({len(chunks)}, {self.dim}); re-index or change embedding_dim"
            )
        super().add(chunks, vectors)

    def save(self) -> None:
        lines = "".join(json.dumps(asdict(c)) + "\n" for c in self._chunks)
        _atomic_write(self._chunks_path, lambda fh: fh.write(lines.encode()))
        _atomic_write(self._vectors_path, lambda fh: np.save(fh, self._matrix))

    def add(self, chunks, vectors) -> None:
        super().add(chunks, vectors)
        self.save()

    def delete_document(self, doc_id: str) -> int:
        removed = super().delete_document(doc_id)
        if removed:
            self.save()
        return removed
