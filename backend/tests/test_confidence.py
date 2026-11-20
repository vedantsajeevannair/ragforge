from app.generation.citations import Citation
from app.generation.confidence import answer_confidence, cited_sentence_ratio, confidence_label
from app.vectorstore.base import SearchHit, StoredChunk

CITE = [Citation(1, "c", "d", "s", "")]


def test_cited_sentence_ratio():
    assert cited_sentence_ratio("One [1]. Two. Three [2].") == 2 / 3
    assert cited_sentence_ratio("") == 0.0


def test_confidence_high_when_covered_and_cited():
    hits = [SearchHit(StoredChunk("c", "d", "BM25 ranks documents by term frequency"), 1.0)]
    score = answer_confidence("How does BM25 rank documents?", "It uses tf [1].", hits, CITE)
    assert score == 1.0 and confidence_label(score) == "high"


def test_confidence_zero_without_citations():
    hits = [SearchHit(StoredChunk("c", "d", "x"), 1.0)]
    assert answer_confidence("q", "a", hits, []) == 0.0
    assert confidence_label(0.5) == "medium" and confidence_label(0.1) == "low"
