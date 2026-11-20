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
    assert body["citations"][0]["source"].startswith("fusion.md")


def test_ask_validates_k(client, loaded):
    assert client.post("/ask", headers=loaded, json={"query": "x", "k": 0}).status_code == 422


def test_query_requires_auth(client):
    assert client.post("/search", json={"query": "x"}).status_code == 401


def test_ask_is_rate_limited(admin_headers):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(jwt_secret="s" * 40, embedding_dim=64, ask_rate_per_minute=2)
    with TestClient(create_app(settings, in_memory=True)) as c:
        r = c.post("/auth/register", json={"username": "zed", "password": "password123"})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        codes = [c.post("/ask", headers=h, json={"query": "anything"}).status_code
                 for _ in range(3)]
    assert codes == [200, 200, 429]


def test_history_and_feedback(client, loaded, user_headers):
    qid = client.post("/ask", headers=loaded, json={"query": "rank fusion"}).json()["query_id"]
    hist = client.get("/history", headers=loaded).json()
    assert hist[0]["id"] == qid and hist[0]["question"] == "rank fusion"
    assert client.get("/history", headers=user_headers).json() == []
    ok = client.post(f"/history/{qid}/feedback", headers=loaded, json={"value": 1})
    assert ok.status_code == 204
    assert client.get("/history", headers=loaded).json()[0]["feedback"] == 1
    other = client.post(f"/history/{qid}/feedback", headers=user_headers, json={"value": -1})
    assert other.status_code == 404
    bad = client.post(f"/history/{qid}/feedback", headers=loaded, json={"value": 3})
    assert bad.status_code == 422


def _parse_sse(text):
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        import json
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_ask_stream_sends_sse_events(client, loaded):
    resp = client.post("/ask/stream", headers=loaded, json={"query": "rank fusion merges"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(resp.text)
    assert events[0][0] == "sources"
    assert events[-1][0] == "done" and events[-1][1]["grounded"]
    assert client.get("/history", headers=loaded).json()[0]["id"] == events[-1][1]["query_id"]


def test_followup_uses_previous_question(client, loaded):
    body = {"query": "What does it merge?", "k": 1, "mode": "bm25",
            "previous_questions": ["Tell me about reciprocal rank fusion"]}
    hits = client.post("/search", headers=loaded, json=body).json()["hits"]
    assert hits[0]["metadata"]["source"] == "fusion.md"
