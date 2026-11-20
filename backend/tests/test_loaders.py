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
