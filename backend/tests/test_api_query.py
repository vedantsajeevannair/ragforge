import pytest

DOCS = {
    "fusion.md": b"# Fusion\nReciprocal rank fusion merges ranked lists from several retrievers.",
    "bread.txt": b"Sourdough bread needs a starter and a long, slow fermentation.",
}


@pytest.fixture
def loaded(client, admin_headers):
    for name, data in DOCS.items():
        coll = "food" if "bread" in name else "ir"
        r = client.post("/documents", headers=admin_headers, files={"file": (name, data)},
                        data={"collection": coll})
        assert r.status_code == 201
    return admin_headers


def test_search_returns_ranked_hits(client, loaded):
    resp = client.post("/search", headers=loaded, json={"query": "rank fusion", "k": 2})
    assert resp.status_code == 200
    hits = resp.json()["hits"]
    assert hits[0]["metadata"]["source"] == "fusion.md"


def test_search_collection_filter(client, loaded):
    body = {"query": "fusion", "collection": "food"}
    hits = client.post("/search", headers=loaded, json=body).json()["hits"]
    assert all(h["metadata"]["collection"] == "food" for h in hits)


def test_ask_returns_cited_answer(client, loaded):
    resp = client.post("/ask", headers=loaded,
                       json={"query": "What does reciprocal rank fusion merge?"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["grounded"] is True
    assert "ranked lists" in body["answer"]
    assert body["citations"][0]["source"] == "fusion.md"


def test_ask_validates_k(client, loaded):
    assert client.post("/ask", headers=loaded, json={"query": "x", "k": 0}).status_code == 422


def test_query_requires_auth(client):
    assert client.post("/search", json={"query": "x"}).status_code == 401
