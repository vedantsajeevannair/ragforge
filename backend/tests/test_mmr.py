import numpy as np
import pytest

from app.embeddings.hashing import HashingEmbedder
from app.retrieval.mmr import mmr, mmr_rerank
from app.vectorstore.base import SearchHit, StoredChunk


def test_mmr_skips_duplicate_when_diversity_matters():
    q = np.array([1.0, 0.0])
    docs = np.array([[1.0, 0.0], [1.0, 0.0], [0.6, 0.8]])
    assert mmr(q, docs, k=2, lambda_=0.4) == [0, 2]


def test_mmr_lambda_one_is_pure_relevance():
    q = np.array([1.0, 0.0])
    docs = np.array([[0.6, 0.8], [1.0, 0.0], [0.99, 0.14]])
    assert mmr(q, docs, k=3, lambda_=1.0) == [1, 2, 0]


def test_mmr_validates_lambda():
    with pytest.raises(ValueError):
        mmr(np.ones(2), np.ones((1, 2)), 1, lambda_=2)


def test_mmr_rerank_returns_hits():
    hits = [SearchHit(StoredChunk(str(i), "d", t), 1.0) for i, t in
            enumerate(["vector search", "vector search", "bm25 lexical ranking"])]
    out = mmr_rerank("vector search ranking", hits, HashingEmbedder(256), k=2, lambda_=0.3)
    assert len(out) == 2
    assert {h.chunk.text for h in out} == {"vector search", "bm25 lexical ranking"}
