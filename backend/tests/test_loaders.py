import pytest

from app.ingestion.loaders import UnsupportedFileType, load_bytes, supported_extensions


def test_text_loader_decodes_utf8():
    doc = load_bytes("héllo".encode(), "notes.txt")
    assert doc.text == "héllo"
    assert doc.metadata["type"] == "text"


def test_markdown_loader_sets_type():
    doc = load_bytes(b"# Title", "README.md")
    assert doc.metadata["type"] == "markdown"


def test_unknown_extension_raises():
    with pytest.raises(UnsupportedFileType):
        load_bytes(b"x", "data.xyz")


def test_supported_extensions_lists_registered_types():
    assert ".txt" in supported_extensions()


def test_html_loader_extracts_visible_text_and_title():
    html = b"<html><head><title>Guide</title><style>p{}</style></head>" \
        b"<body><p>Hello</p><script>evil()</script><p>World</p></body></html>"
    doc = load_bytes(html, "page.html")
    assert "Hello" in doc.text and "World" in doc.text
    assert "evil" not in doc.text
    assert doc.metadata["title"] == "Guide"


def test_pdf_loader_reads_pages(fixtures_dir):
    doc = load_bytes((fixtures_dir / "sample.pdf").read_bytes(), "sample.pdf")
    assert doc.metadata["pages"] == 2
    assert "vector search" in doc.text
    assert "BM25" in doc.text
    assert doc.metadata["page_offsets"][0] == 0


def test_docx_loader_maps_headings(fixtures_dir):
    doc = load_bytes((fixtures_dir / "policy.docx").read_bytes(), "policy.docx")
    assert doc.text.splitlines()[0] == "# Leave Policy"
    assert "## Carry over" in doc.text
    assert "24 days" in doc.text


def test_docx_loader_rejects_non_zip():
    with pytest.raises(ValueError, match="docx"):
        load_bytes(b"not a zip", "x.docx")
