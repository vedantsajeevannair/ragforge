import pytest

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.embeddings.hashing import HashingEmbedder
from app.eval.dataset import EvalExample
from app.eval.runner import evaluate_answers, evaluate_retrieval
from app.generation.answer import AnswerEngine
from app.generation.extractive import ExtractiveProvider
from app.ingestion.pipeline import ingest_bytes
from app.vectorstore.memory import InMemoryVectorStore


@pytest.fixture
def kb():
    base = KnowledgeBase(HashingEmbedder(512), InMemoryVectorStore(512))
    base.add(ingest_bytes(b"BM25 scores documents using term frequency and idf.", "bm25.txt"))
    base.add(ingest_bytes(b"Cosine similarity compares embedding vectors.", "cosine.txt"))
    return base


EXAMPLES = [
    EvalExample("How does BM25 score documents?", ["bm25.txt"], ["term frequency"]),
    EvalExample("What compares embedding vectors?", ["cosine.txt"], ["cosine similarity"]),
]


def test_retrieval_eval_perfect_on_easy_set(kb):
    report = evaluate_retrieval(kb, EXAMPLES, SearchOptions(k=2))
    assert report.n == 2
    assert report.metrics["hit@1"] == 1.0
    assert report.metrics["mrr"] == 1.0
    assert report.per_question[0]["ranked_sources"][0] == "bm25.txt"


def test_answer_eval(kb):
    m = evaluate_answers(AnswerEngine(kb, ExtractiveProvider()), EXAMPLES, SearchOptions(k=2))
    assert m["grounded_rate"] == 1.0
    assert m["phrase_recall"] == 1.0
    assert m["citation_precision"] > 0.5
