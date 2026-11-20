from app.retrieval.rerank import phrase_bonus, rerank, term_coverage
from app.vectorstore.base import SearchHit, StoredChunk


def test_term_coverage():
    assert term_coverage("vector search speed", "fast vector search") == 2 / 3
    assert term_coverage("the", "anything") == 0.0


def test_phrase_bonus():
    assert phrase_bonus("reciprocal rank fusion", "uses reciprocal rank scores") == 1.0
    assert phrase_bonus("rank reciprocal", "uses reciprocal rank") == 0.0


def test_rerank_promotes_full_coverage():
    hits = [SearchHit(StoredChunk("a", "d", "vector only"), 1.0),
            SearchHit(StoredChunk("b", "d", "vector search latency"), 0.8)]
    assert rerank("vector search latency", hits)[0].chunk.chunk_id == "b"
