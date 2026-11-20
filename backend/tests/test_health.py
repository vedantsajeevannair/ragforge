def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_responses_carry_request_id_and_timing(client):
    resp = client.get("/health", headers={"x-request-id": "abc123"})
    assert resp.headers["x-request-id"] == "abc123"
    assert resp.headers["server-timing"].startswith("app;dur=")


def test_request_id_generated_when_missing(client):
    assert len(client.get("/health").headers["x-request-id"]) == 12
