import numpy as np
import pytest

from app.vectorstore.base import StoredChunk
from app.vectorstore.memory import InMemoryVectorStore


def _unit(*xs):
    v = np.array(xs, dtype=np.float32)
    return v / np.linalg.norm(v)


def _chunk(cid, doc="d1", **meta):
    return StoredChunk(chunk_id=cid, doc_id=doc, text=cid, metadata=meta)


@pytest.fixture
def store():
    s = InMemoryVectorStore(dim=2)
    s.add([_chunk("a", type="pdf"), _chunk("b", type="md"), _chunk("c", doc="d2", type="pdf")],
          np.stack([_unit(1, 0), _unit(0, 1), _unit(1, 1)]))
    return s


def test_search_orders_by_cosine(store):
    hits = store.search(_unit(1, 0.1), k=3)
    assert [h.chunk.chunk_id for h in hits] == ["a", "c", "b"]
    assert hits[0].score > hits[1].score > hits[2].score


def test_search_applies_filter(store):
    hits = store.search(_unit(0, 1), k=3, flt={"type": "pdf"})
    assert {h.chunk.chunk_id for h in hits} == {"a", "c"}


def test_upsert_replaces_existing_chunk(store):
    store.add([_chunk("a", type="pdf")], np.stack([_unit(0, 1)]))
    assert len(store) == 3
    assert store.search(_unit(0, 1), k=1)[0].chunk.chunk_id in {"a", "b"}


def test_delete_document(store):
    assert store.delete_document("d1") == 2
    assert [c.chunk_id for c in store.all_chunks()] == ["c"]
    assert store.search(_unit(1, 0), k=5)[0].chunk.chunk_id == "c"


def test_dim_mismatch_raises():
    with pytest.raises(ValueError):
        InMemoryVectorStore(dim=3).add([_chunk("a")], np.ones((1, 2), dtype=np.float32))


def test_empty_store_returns_nothing():
    assert InMemoryVectorStore(dim=2).search(_unit(1, 0), k=3) == []
