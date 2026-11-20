from app.ingestion.models import Chunk
from app.ingestion.pages import assign_pages


def test_assign_pages_uses_start_offset():
    meta = {"page_offsets": [0, 100, 250]}
    chunks = [Chunk("a", "d", 0, 5, 10, dict(meta)), Chunk("b", "d", 1, 120, 130, dict(meta)),
              Chunk("c", "d", 2, 260, 270, dict(meta))]
    assert [c.metadata["page"] for c in assign_pages(chunks)] == [1, 2, 3]
    assert "page_offsets" not in chunks[0].metadata


def test_assign_pages_ignores_non_pdf_chunks():
    chunk = Chunk("a", "d", 0, 0, 1, {})
    assert "page" not in assign_pages([chunk])[0].metadata
