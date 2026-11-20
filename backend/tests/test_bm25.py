from app.retrieval.bm25 import BM25Index
from app.vectorstore.base import StoredChunk


def _index():
    idx = BM25Index()
    idx.add([
        StoredChunk("1", "d", "Python is a programming language used for data science."),
        StoredChunk("2", "d", "Vector databases store embeddings for similarity search."),
        StoredChunk("3", "d", "BM25 ranks documents by term frequency and rarity.",
                    {"type": "pdf"}),
        StoredChunk("4", "d", "Cats sleep most of the day."),
    ])
    return idx


def test_bm25_ranks_relevant_chunk_first():
    hits = _index().search("how does BM25 rank documents", k=2)
    assert hits[0].chunk.chunk_id == "3"


def test_bm25_returns_only_matching_terms():
    assert _index().search("quantum chromodynamics", k=5) == []


def test_bm25_rare_terms_have_higher_idf():
    idx = _index()
    idx.add([StoredChunk("5", "d", "search search search")])
    assert idx.idf("cat") > idx.idf("search")


def test_bm25_filter():
    hits = _index().search("documents embeddings", k=5, flt={"type": "pdf"})
    assert [h.chunk.chunk_id for h in hits] == ["3"]


def test_bm25_rebuild_resets_stats():
    idx = _index()
    idx.rebuild([StoredChunk("x", "d", "single")])
    assert len(idx) == 1 and idx.avg_length == 1


def test_bm25_text_fn_indexes_extra_context():
    idx = BM25Index(text_fn=lambda c: f"{c.metadata.get('section', '')} {c.text}")
    idx.add([StoredChunk("1", "d", "uses k1 and b", {"section": "BM25 parameters"}),
             StoredChunk("2", "d", "unrelated words")])
    assert idx.search("bm25", k=1)[0].chunk.chunk_id == "1"
