import pytest

from app.ingestion.chunking import FixedSizeChunker
from app.ingestion.models import Document


def test_fixed_chunker_respects_size_and_overlap():
    doc = Document(text="abcdefghij" * 3, source="s")
    chunks = FixedSizeChunker(size=10, overlap=2).split(doc)
    assert all(len(c.text) <= 10 for c in chunks)
    assert chunks[0].text[-2:] == chunks[1].text[:2]
    assert chunks[-1].end == len(doc.text)


def test_fixed_chunker_offsets_match_source():
    doc = Document(text="the quick brown fox jumps over the lazy dog", source="s")
    for chunk in FixedSizeChunker(size=12, overlap=3).split(doc):
        assert doc.text[chunk.start:chunk.end] == chunk.text


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, 10), (10, -1)])
def test_fixed_chunker_rejects_bad_params(size, overlap):
    with pytest.raises(ValueError):
        FixedSizeChunker(size=size, overlap=overlap)


def test_empty_document_yields_no_chunks():
    assert FixedSizeChunker(10, 2).split(Document(text="", source="s")) == []
