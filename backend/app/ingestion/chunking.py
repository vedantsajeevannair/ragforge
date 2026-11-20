"""Chunking strategies that split a Document into overlapping Chunks."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.ingestion.models import Chunk, Document


class Chunker(ABC):
    name: str = "base"

    @abstractmethod
    def split(self, document: Document) -> list[Chunk]:
        ...


def _validate(size: int, overlap: int) -> None:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be in [0, size)")


class FixedSizeChunker(Chunker):
    """Splits text into windows of `size` characters with `overlap` characters shared."""

    name = "fixed"

    def __init__(self, size: int = 800, overlap: int = 120) -> None:
        _validate(size, overlap)
        self.size = size
        self.overlap = overlap

    def split(self, document: Document) -> list[Chunk]:
        text = document.text
        chunks: list[Chunk] = []
        step = self.size - self.overlap
        start = 0
        while start < len(text):
            end = min(start + self.size, len(text))
            piece = text[start:end]
            if piece.strip():
                chunks.append(
                    Chunk(piece, document.doc_id, len(chunks), start, end, dict(document.metadata))
                )
            if end == len(text):
                break
            start += step
        return chunks
