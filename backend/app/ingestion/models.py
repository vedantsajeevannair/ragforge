"""Core data models shared by the ingestion pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A loaded source document before chunking."""

    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def doc_id(self) -> str:
        digest = hashlib.sha1(f"{self.source}\0{self.text}".encode()).hexdigest()
        return digest[:16]


@dataclass
class Chunk:
    """A retrievable slice of a document."""

    text: str
    doc_id: str
    index: int
    start: int
    end: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}:{self.index}"
