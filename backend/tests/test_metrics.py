import math

import pytest

from app.eval.metrics import (
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

RANKED = ["a", "x", "b", "y"]
REL = {"a", "b"}


def test_recall_and_precision():
    assert recall_at_k(RANKED, REL, 1) == 0.5
    assert recall_at_k(RANKED, REL, 3) == 1.0
    assert precision_at_k(RANKED, REL, 2) == 0.5
    assert recall_at_k(RANKED, set(), 3) == 0.0


def test_hit_rate_and_mrr():
    assert hit_rate_at_k(RANKED, {"b"}, 2) == 0.0
    assert hit_rate_at_k(RANKED, {"b"}, 3) == 1.0
    assert reciprocal_rank(RANKED, {"b"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(RANKED, {"z"}) == 0.0


def test_ndcg():
    assert ndcg_at_k(["a", "b"], REL, 2) == 1.0
    expected = (1 + 1 / math.log2(4)) / (1 + 1 / math.log2(3))
    assert ndcg_at_k(RANKED, REL, 3) == pytest.approx(expected)
