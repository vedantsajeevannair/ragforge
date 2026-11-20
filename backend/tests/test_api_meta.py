def _upload(client, headers, name, collection):
    client.post("/documents", headers=headers, files={"file": (name, b"some text here")},
                data={"collection": collection})


def test_collections_counts(client, admin_headers):
    _upload(client, admin_headers, "a.txt", "x")
    _upload(client, admin_headers, "b.txt", "x")
    _upload(client, admin_headers, "c.txt", "y")
    resp = client.get("/collections", headers=admin_headers).json()
    assert resp == [{"name": "x", "documents": 2}, {"name": "y", "documents": 1}]


def test_stats_admin_only(client, admin_headers, user_headers):
    assert client.get("/stats", headers=user_headers).status_code == 403
    stats = client.get("/stats", headers=admin_headers).json()
    assert stats["users"] == 2


def test_config_lists_capabilities(client, admin_headers):
    cfg = client.get("/config", headers=admin_headers).json()
    assert ".pdf" in cfg["supported_extensions"]
    assert "recursive" in cfg["chunkers"]
    assert cfg["llm_provider"] == "extractive"
