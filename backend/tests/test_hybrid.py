import pytest

from app.retrieval.base import Retriever
from app.retrieval.hybrid import HybridRetriever, reciprocal_rank_fusion
from app.vectorstore.base import SearchHit, StoredChunk


def _hits(*ids):
    return [SearchHit(StoredChunk(i, "d", i), 1.0) for i in ids]


def test_rrf_rewards_agreement():
    fused = reciprocal_rank_fusion([_hits("a", "b", "c"), _hits("b", "a", "d")])
    assert [h.chunk.chunk_id for h in fused][:2] in (["a", "b"], ["b", "a"])
    assert fused[-1].chunk.chunk_id in {"c", "d"}


def test_rrf_weights_shift_order():
    fused = reciprocal_rank_fusion([_hits("a"), _hits("b")], weights=[1.0, 3.0])
    assert fused[0].chunk.chunk_id == "b"


def test_rrf_weight_count_must_match():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([_hits("a")], weights=[1, 2])


class _Fixed(Retriever):
    def __init__(self, ids):
        self.ids = ids
        self.asked = None

    def retrieve(self, query, k, flt=None):
        self.asked = k
        return _hits(*self.ids)[:k]


def test_hybrid_requests_larger_candidate_pool_and_truncates():
    r1, r2 = _Fixed(["a", "b", "c"]), _Fixed(["c", "d"])
    out = HybridRetriever([r1, r2], candidate_multiplier=3).retrieve("q", k=2)
    assert r1.asked == 6
    assert len(out) == 2 and out[0].chunk.chunk_id == "c"


def test_hybrid_needs_retrievers():
    with pytest.raises(ValueError):
        HybridRetriever([])
