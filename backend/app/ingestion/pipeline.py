"""End-to-end ingestion: bytes -> cleaned Document -> Chunks."""

from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.chunking import get_chunker
from app.ingestion.cleaning import clean_text
from app.ingestion.loaders import load_bytes
from app.ingestion.models import Chunk, Document
from app.ingestion.pages import assign_pages


@dataclass
class IngestResult:
    document: Document
    chunks: list[Chunk]


def _fingerprint(text: str) -> str:
    return " ".join(text.lower().split())


def drop_duplicate_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """Remove chunks whose normalised text repeats an earlier chunk (boilerplate,
    repeated headers/footers in PDFs) and renumber the rest."""
    seen: set[str] = set()
    kept: list[Chunk] = []
    for chunk in chunks:
        key = _fingerprint(chunk.text)
        if key in seen:
            continue
        seen.add(key)
        chunk.index = len(kept)
        kept.append(chunk)
    return kept


def default_strategy(document: Document) -> str:
    return "markdown" if document.metadata.get("type") == "markdown" else "recursive"


def ingest_bytes(
    data: bytes,
    filename: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    strategy: str | None = None,
) -> IngestResult:
    raw = load_bytes(data, filename)
    if raw.metadata.get("type") == "pdf":
        # Cleaning shifts offsets, so clean page by page and rebuild offsets.
        pages = raw.text.split("\n\n")
        cleaned_pages = [clean_text(p) for p in pages]
        offsets, pos = [], 0
        for page in cleaned_pages:
            offsets.append(pos)
            pos += len(page) + 2
        raw.metadata["page_offsets"] = offsets
        text = "\n\n".join(cleaned_pages)
    else:
        text = clean_text(raw.text)
    document = Document(text=text, source=raw.source, metadata=raw.metadata)
    chunker = get_chunker(strategy or default_strategy(document), chunk_size, chunk_overlap)
    chunks = drop_duplicate_chunks(assign_pages(chunker.split(document)))
    document.metadata.pop("page_offsets", None)
    return IngestResult(document=document, chunks=chunks)
