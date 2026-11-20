"""Map chunk offsets back to PDF page numbers."""

from bisect import bisect_right

from app.ingestion.models import Chunk


def assign_pages(chunks: list[Chunk]) -> list[Chunk]:
    """Set `page` (1-based) on chunks whose metadata carries PDF page offsets."""
    for chunk in chunks:
        offsets = chunk.metadata.get("page_offsets")
        if offsets:
            chunk.metadata["page"] = bisect_right(offsets, chunk.start)
            chunk.metadata.pop("page_offsets", None)
    return chunks
