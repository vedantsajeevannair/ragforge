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
