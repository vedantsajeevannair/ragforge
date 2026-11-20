import pytest

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.embeddings.hashing import HashingEmbedder
from app.generation.answer import AnswerEngine
from app.generation.extractive import NOT_FOUND, ExtractiveProvider
from app.generation.providers import LLMProvider
from app.ingestion.pipeline import ingest_bytes
from app.vectorstore.memory import InMemoryVectorStore


@pytest.fixture
def kb():
    base = KnowledgeBase(HashingEmbedder(512), InMemoryVectorStore(512))
    base.add(ingest_bytes(b"Reciprocal rank fusion merges ranked lists from several "
                          b"retrievers. It needs no score calibration.", "rrf.txt"))
    base.add(ingest_bytes(b"Sourdough needs a starter and a long fermentation.", "bread.txt"))
    return base


def test_extractive_answer_is_grounded_with_citation(kb):
    ans = AnswerEngine(kb, ExtractiveProvider()).answer("What does reciprocal rank fusion merge?")
    assert "ranked lists" in ans.answer
    assert ans.grounded
    assert ans.citations[0].source == "rrf.txt"
    assert set(ans.timings_ms) == {"retrieval", "generation"}


class _Echo(LLMProvider):
    def complete(self, system, user):
        return "Made up [1] and bogus [42]."


def test_invalid_markers_are_removed(kb):
    ans = AnswerEngine(kb, _Echo()).answer("rank fusion", SearchOptions(k=1))
    assert "[42]" not in ans.answer
    assert [c.number for c in ans.citations] == [1]


def test_min_score_returns_not_found(kb):
    ans = AnswerEngine(kb, ExtractiveProvider(), min_score=10.0).answer("rank fusion")
    assert ans.answer == NOT_FOUND and not ans.grounded and ans.hits == []
