from app.generation.citations import cited_numbers, resolve_citations, strip_invalid_markers
from app.vectorstore.base import SearchHit, StoredChunk

HITS = [SearchHit(StoredChunk(f"d:{i}", "d", f"text {i}", {"source": "f.md"}), 1.0)
        for i in range(2)]


def test_cited_numbers_dedupes_in_order():
    assert cited_numbers("A [2]. B [1][2]. C [2].") == [2, 1]


def test_resolve_citations_ignores_out_of_range():
    cites = resolve_citations("Claim [1] and [7].", HITS)
    assert [c.number for c in cites] == [1]
    assert cites[0].chunk_id == "d:0" and cites[0].source == "f.md"


def test_snippet_is_truncated():
    long = [SearchHit(StoredChunk("x", "d", "word " * 100, {}), 1.0)]
    assert resolve_citations("[1]", long, snippet_chars=20)[0].snippet.endswith("…")


def test_strip_invalid_markers():
    assert strip_invalid_markers("ok [1] bad [9]", 2) == "ok [1] bad "


def test_snippet_drops_markdown_headings():
    hits = [SearchHit(StoredChunk("x", "d", "## Title\nBody text.", {}), 1.0)]
    assert resolve_citations("[1]", hits)[0].snippet == "Body text."
