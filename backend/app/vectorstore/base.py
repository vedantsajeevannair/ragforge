"""Vector store interface and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class StoredChunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    chunk: StoredChunk
    score: float


MetadataFilter = dict[str, Any]


def matches(metadata: dict[str, Any], flt: MetadataFilter | None) -> bool:
    """Exact-match filter; a list value means 'any of'.

    The special key "$or" takes a list of sub-filters, at least one of which must match.
    """
    if not flt:
        return True
    for key, expected in flt.items():
        if key == "$or":
            if not any(matches(metadata, sub) for sub in expected):
                return False
            continue
        value = metadata.get(key)
        if isinstance(expected, list | tuple | set):
            if value not in expected:
                return False
        elif value != expected:
            return False
    return True


class VectorStore(ABC):
    dim: int

    @abstractmethod
    def add(self, chunks: list[StoredChunk], vectors: np.ndarray) -> None: ...

    @abstractmethod
    def search(self, vector: np.ndarray, k: int,
               flt: MetadataFilter | None = None) -> list[SearchHit]: ...

    @abstractmethod
    def delete_document(self, doc_id: str) -> int: ...

    @abstractmethod
    def all_chunks(self) -> list[StoredChunk]: ...

    def update_metadata(self, doc_id: str, changes: dict[str, Any]) -> int:
        """Merge `changes` into the metadata of every chunk of a document."""
        n = 0
        for chunk in self.all_chunks():
            if chunk.doc_id == doc_id:
                chunk.metadata.update(changes)
                n += 1
        return n

    def __len__(self) -> int:
        return len(self.all_chunks())
