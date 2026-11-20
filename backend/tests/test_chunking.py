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


from app.ingestion.chunking import RecursiveChunker  # noqa: E402


def test_recursive_chunker_prefers_paragraph_boundaries():
    paras = ["Paragraph one is here.", "Paragraph two is here.", "Paragraph three."]
    doc = Document(text="\n\n".join(paras), source="s")
    chunks = RecursiveChunker(size=30, overlap=0).split(doc)
    assert chunks[0].text.strip() == paras[0]


def test_recursive_chunker_never_exceeds_size():
    doc = Document(text=("word " * 500).strip(), source="s")
    chunks = RecursiveChunker(size=50, overlap=10).split(doc)
    assert chunks
    assert max(len(c.text) for c in chunks) <= 50


def test_recursive_chunker_offsets_match_source():
    doc = Document(text="Alpha beta.\n\nGamma delta epsilon. Zeta eta theta.\nIota.", source="s")
    for chunk in RecursiveChunker(size=20, overlap=5).split(doc):
        assert doc.text[chunk.start:chunk.end] == chunk.text


def test_recursive_chunker_covers_whole_text():
    text = "x" * 333
    chunks = RecursiveChunker(size=100, overlap=0).split(Document(text=text, source="s"))
    assert "".join(c.text for c in chunks) == text


from app.ingestion.chunking import SentenceChunker, split_sentences  # noqa: E402


def test_split_sentences_spans():
    text = "First one. Second one! Third? yes"
    parts = [text[s:e] for s, e in split_sentences(text)]
    assert parts == ["First one.", "Second one!", "Third? yes"]


def test_sentence_chunker_keeps_sentences_whole_with_overlap():
    text = "Alpha is first. Beta is second. Gamma is third. Delta is fourth."
    chunks = SentenceChunker(size=35, overlap_sentences=1).split(Document(text=text, source="s"))
    assert chunks[0].text == "Alpha is first. Beta is second."
    assert chunks[1].text.startswith("Beta is second.")
