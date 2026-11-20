from app.ingestion.pipeline import ingest_bytes


def test_ingest_markdown_uses_section_chunking():
    md = b"# Title\nSome   intro.\n\n## Part\nBody text here."
    result = ingest_bytes(md, "doc.md", chunk_size=200, chunk_overlap=0)
    assert result.chunks
    assert any(c.metadata.get("section") == "Title > Part" for c in result.chunks)
    assert "Some intro." in result.document.text


def test_ingest_pdf_assigns_pages(fixtures_dir):
    data = (fixtures_dir / "sample.pdf").read_bytes()
    result = ingest_bytes(data, "sample.pdf", chunk_size=40, chunk_overlap=0)
    pages = {c.metadata["page"] for c in result.chunks}
    assert pages == {1, 2}
    assert "page_offsets" not in result.document.metadata


def test_ingest_respects_explicit_strategy():
    result = ingest_bytes(b"a" * 50, "x.txt", chunk_size=20, chunk_overlap=0, strategy="fixed")
    assert len(result.chunks) == 3
