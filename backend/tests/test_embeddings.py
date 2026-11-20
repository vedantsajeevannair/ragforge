import numpy as np

from app.embeddings.hashing import HashingEmbedder


def test_hashing_embedder_shape_and_norm():
    emb = HashingEmbedder(dim=64).embed(["hello world", "another text"])
    assert emb.shape == (2, 64)
    assert np.allclose(np.linalg.norm(emb, axis=1), 1.0, atol=1e-5)


def test_hashing_embedder_is_deterministic():
    e = HashingEmbedder(dim=128)
    assert np.array_equal(e.embed_one("vector search"), e.embed_one("vector search"))


def test_similar_texts_score_higher_than_unrelated():
    e = HashingEmbedder(dim=512)
    q = e.embed_one("how does vector search work")
    near = e.embed_one("vector search finds nearest neighbours")
    far = e.embed_one("bake the bread at two hundred degrees")
    assert q @ near > q @ far


def test_char_ngrams_give_partial_credit_for_morphology():
    e = HashingEmbedder(dim=512)
    assert e.embed_one("tokenizer") @ e.embed_one("tokenization") > 0.3


def test_empty_text_gives_zero_vector():
    assert not HashingEmbedder(dim=32).embed_one("").any()


import httpx  # noqa: E402
import pytest  # noqa: E402

from app.embeddings.http import HTTPEmbedder  # noqa: E402


def _mock_client(dim, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        import json
        body = json.loads(request.content)
        calls.append(len(body["input"]))
        data = [{"index": i, "embedding": [float(i + 1)] * dim}
                for i in range(len(body["input"]))][::-1]
        return httpx.Response(200, json={"data": data})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_http_embedder_batches_and_orders_results():
    calls = []
    e = HTTPEmbedder("http://x/v1", "m", dim=4, batch_size=2, client=_mock_client(4, calls))
    out = e.embed(["a", "b", "c"])
    assert calls == [2, 1]
    assert out.shape == (3, 4)
    assert np.allclose(np.linalg.norm(out, axis=1), 1.0)


def test_http_embedder_rejects_wrong_dim():
    e = HTTPEmbedder("http://x/v1", "m", dim=8, client=_mock_client(4, []))
    with pytest.raises(ValueError):
        e.embed(["a"])


def test_http_embedder_empty_input():
    e = HTTPEmbedder("http://x/v1", "m", dim=8, client=_mock_client(8, []))
    assert e.embed([]).shape == (0, 8)


from app.embeddings.cache import CachedEmbedder  # noqa: E402


def test_cached_embedder_counts_hits_and_matches_inner():
    inner = HashingEmbedder(dim=32)
    cached = CachedEmbedder(inner, max_items=10)
    first = cached.embed(["a b", "c d"])
    second = cached.embed(["a b"])
    assert cached.misses == 2 and cached.hits == 1
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], inner.embed_one("c d"))


def test_cached_embedder_evicts_oldest():
    cached = CachedEmbedder(HashingEmbedder(dim=16), max_items=2)
    for word in ("one", "two", "three"):
        cached.embed([word])
    assert "one" not in cached._cache


from app.config import Settings  # noqa: E402
from app.embeddings.factory import build_embedder  # noqa: E402


def test_factory_builds_hashing_by_default():
    e = build_embedder(Settings(embedding_dim=64))
    assert e.dim == 64 and e.name == "cached-hashing"


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        build_embedder(Settings(embedding_provider="magic"))
