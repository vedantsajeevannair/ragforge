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


class RecursiveChunker(Chunker):
    """Splits on the coarsest separator that keeps pieces under `size`, then merges.

    Tries paragraphs first, then lines, sentences and words, so chunk boundaries
    tend to fall on natural breaks instead of mid-word.
    """

    name = "recursive"
    separators = ("\n\n", "\n", ". ", " ")

    def __init__(self, size: int = 800, overlap: int = 120) -> None:
        _validate(size, overlap)
        self.size = size
        self.overlap = overlap

    def _segments(self, text: str, start: int, level: int) -> list[tuple[int, int]]:
        if len(text) <= self.size:
            return [(start, start + len(text))]
        if level >= len(self.separators):
            return [(start + i, start + min(i + self.size, len(text)))
                    for i in range(0, len(text), self.size)]
        sep = self.separators[level]
        spans: list[tuple[int, int]] = []
        pos = 0
        for part in text.split(sep):
            end = pos + len(part) + len(sep)
            end = min(end, len(text))
            piece = text[pos:end]
            if len(piece) > self.size:
                spans.extend(self._segments(piece, start + pos, level + 1))
            elif piece:
                spans.append((start + pos, start + end))
            pos = end
        return spans

    def split(self, document: Document) -> list[Chunk]:
        text = document.text
        spans = self._segments(text, 0, 0)
        merged: list[tuple[int, int]] = []
        cur_start, cur_end = None, None
        for s, e in spans:
            if cur_start is None:
                cur_start, cur_end = s, e
            elif e - cur_start <= self.size:
                cur_end = e
            else:
                merged.append((cur_start, cur_end))
                back = max(cur_end - self.overlap, cur_start)
                cur_start = back if e - back <= self.size else s
                cur_end = e
        if cur_start is not None:
            merged.append((cur_start, cur_end))
        chunks = []
        for s, e in merged:
            if text[s:e].strip():
                chunks.append(Chunk(text[s:e], document.doc_id, len(chunks), s, e,
                                    dict(document.metadata)))
        return chunks


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) spans of sentences in `text`."""
    spans, pos = [], 0
    for match in _SENTENCE_END.finditer(text):
        spans.append((pos, match.start()))
        pos = match.end()
    if pos < len(text):
        spans.append((pos, len(text)))
    return [(s, e) for s, e in spans if text[s:e].strip()]


class SentenceChunker(Chunker):
    """Packs whole sentences into chunks, overlapping by `overlap_sentences`."""

    name = "sentence"

    def __init__(self, size: int = 800, overlap_sentences: int = 1) -> None:
        if size <= 0:
            raise ValueError("chunk size must be positive")
        if overlap_sentences < 0:
            raise ValueError("overlap_sentences must be >= 0")
        self.size = size
        self.overlap_sentences = overlap_sentences

    def split(self, document: Document) -> list[Chunk]:
        text = document.text
        sentences = split_sentences(text)
        chunks: list[Chunk] = []
        i = 0
        while i < len(sentences):
            j = i
            while j + 1 < len(sentences) and sentences[j + 1][1] - sentences[i][0] <= self.size:
                j += 1
            s, e = sentences[i][0], sentences[j][1]
            chunks.append(Chunk(text[s:e], document.doc_id, len(chunks), s, e,
                                dict(document.metadata)))
            if j + 1 >= len(sentences):
                break
            i = max(j + 1 - self.overlap_sentences, i + 1)
        return chunks
