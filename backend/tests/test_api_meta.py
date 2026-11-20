def _upload(client, headers, name, collection):
    client.post("/documents", headers=headers, files={"file": (name, b"some text here")},
                data={"collection": collection})


def test_collections_counts(client, admin_headers):
    _upload(client, admin_headers, "a.txt", "x")
    _upload(client, admin_headers, "b.txt", "x")
    _upload(client, admin_headers, "c.txt", "y")
    resp = client.get("/collections", headers=admin_headers).json()
    assert [(r["name"], r["documents"]) for r in resp] == [("x", 2), ("y", 1)]
    assert all(r["chunks"] >= r["documents"] for r in resp)


def test_stats_admin_only(client, admin_headers, user_headers):
    assert client.get("/stats", headers=user_headers).status_code == 403
    stats = client.get("/stats", headers=admin_headers).json()
    assert stats["users"] == 2


def test_config_lists_capabilities(client, admin_headers):
    cfg = client.get("/config", headers=admin_headers).json()
    assert ".pdf" in cfg["supported_extensions"]
    assert "recursive" in cfg["chunkers"]
    assert cfg["llm_provider"] == "extractive"


def test_stats_include_query_metrics(client, admin_headers):
    client.post("/ask", headers=admin_headers, json={"query": "nothing indexed"})
    stats = client.get("/stats", headers=admin_headers).json()
    assert stats["queries"] == 1 and stats["grounded_rate"] == 0.0
