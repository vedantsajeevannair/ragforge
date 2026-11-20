MD = b"# Retrieval\nHybrid search combines BM25 and dense vectors.\n## Fusion\nRRF merges ranks."


def _upload(client, headers, name="guide.md", data=MD, collection="default"):
    return client.post("/documents", headers=headers, files={"file": (name, data)},
                       data={"collection": collection})


def test_upload_and_list(client, admin_headers):
    resp = _upload(client, admin_headers)
    assert resp.status_code == 201, resp.text
    doc = resp.json()
    assert doc["doc_type"] == "markdown" and doc["chunk_count"] >= 1
    listed = client.get("/documents", headers=admin_headers).json()
    assert [d["doc_id"] for d in listed] == [doc["doc_id"]]


def test_upload_requires_auth(client):
    assert _upload(client, {}).status_code == 401


def test_upload_rejects_unsupported_and_empty(client, admin_headers):
    assert _upload(client, admin_headers, name="x.exe", data=b"MZ").status_code == 415
    assert _upload(client, admin_headers, data=b"").status_code == 400


def test_upload_rejects_bad_collection_name(client, admin_headers):
    assert _upload(client, admin_headers, collection="bad name!").status_code == 422


def test_filter_by_collection(client, admin_headers):
    _upload(client, admin_headers, collection="a")
    _upload(client, admin_headers, name="other.txt", data=b"unrelated text", collection="b")
    docs = client.get("/documents?collection=b", headers=admin_headers).json()
    assert [d["filename"] for d in docs] == ["other.txt"]


def test_get_chunks_in_order(client, admin_headers):
    doc_id = _upload(client, admin_headers).json()["doc_id"]
    chunks = client.get(f"/documents/{doc_id}/chunks", headers=admin_headers).json()
    starts = [c["metadata"]["start"] for c in chunks]
    assert starts == sorted(starts)


def test_delete_permissions(client, admin_headers, user_headers):
    doc_id = _upload(client, admin_headers).json()["doc_id"]
    assert client.delete(f"/documents/{doc_id}", headers=user_headers).status_code == 403
    assert client.delete(f"/documents/{doc_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/documents/{doc_id}", headers=admin_headers).status_code == 404


def test_owner_can_delete_own_document(client, user_headers):
    doc_id = _upload(client, user_headers).json()["doc_id"]
    assert client.delete(f"/documents/{doc_id}", headers=user_headers).status_code == 204


def test_upload_sanitises_filename(client, admin_headers):
    resp = _upload(client, admin_headers, name="../../secret notes.md")
    assert resp.json()["filename"] == "secret_notes.md"


def test_download_original(tmp_path, admin_headers):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(data_dir=tmp_path, jwt_secret="d" * 40, embedding_dim=64)
    with TestClient(create_app(settings)) as c:
        token = c.post("/auth/register", json={"username": "ann", "password": "password123"})
        h = {"Authorization": f"Bearer {token.json()['access_token']}"}
        doc_id = c.post("/documents", headers=h, files={"file": ("a.md", MD)}).json()["doc_id"]
        resp = c.get(f"/documents/{doc_id}/download", headers=h)
        assert resp.content == MD
        assert 'filename="a.md"' in resp.headers["content-disposition"]
        c.delete(f"/documents/{doc_id}", headers=h)
        assert not (tmp_path / "files" / doc_id).exists()


def test_download_unavailable_in_memory(client, admin_headers):
    doc_id = _upload(client, admin_headers).json()["doc_id"]
    assert client.get(f"/documents/{doc_id}/download", headers=admin_headers).status_code == 404


def test_reindex_uses_new_chunk_size(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    text = ("Sentence about retrieval. " * 60).encode()
    base = dict(data_dir=tmp_path, jwt_secret="r" * 40, embedding_dim=64, chunk_overlap=0)
    with TestClient(create_app(Settings(**base, chunk_size=1000))) as c:
        token = c.post("/auth/register", json={"username": "ann", "password": "password123"})
        h = {"Authorization": f"Bearer {token.json()['access_token']}"}
        before = c.post("/documents", headers=h, files={"file": ("a.txt", text)}).json()
    with TestClient(create_app(Settings(**base, chunk_size=200))) as c:
        token = c.post("/auth/login", json={"username": "ann", "password": "password123"})
        h = {"Authorization": f"Bearer {token.json()['access_token']}"}
        assert c.post("/documents/reindex", headers=h).json() == {"reindexed": 1, "skipped": []}
        after = c.get(f"/documents/{before['doc_id']}", headers=h).json()
        assert after["chunk_count"] > before["chunk_count"]
        assert c.post("/search", headers=h, json={"query": "retrieval"}).json()["hits"]


def test_list_documents_paginates(client, admin_headers):
    for i in range(5):
        _upload(client, admin_headers, name=f"f{i}.txt", data=f"text number {i}".encode())
    page = client.get("/documents?limit=2&offset=2", headers=admin_headers)
    assert page.headers["x-total-count"] == "5"
    assert len(page.json()) == 2
    assert client.get("/documents?limit=0", headers=admin_headers).status_code == 422


def test_upload_rejects_renamed_binary(client, admin_headers):
    resp = _upload(client, admin_headers, name="report.pdf", data=b"MZ\x90\x00not a pdf")
    assert resp.status_code == 415
    assert "not a valid .pdf" in resp.json()["detail"]


def test_patch_moves_collection_and_changes_visibility(client, admin_headers, user_headers):
    doc_id = _upload(client, user_headers, collection="a").json()["doc_id"]
    resp = client.patch(f"/documents/{doc_id}", headers=user_headers,
                        json={"collection": "b", "visibility": "private", "title": "Guide"})
    assert resp.status_code == 200
    assert resp.json()["collection"] == "b" and resp.json()["title"] == "Guide"
    hits = client.post("/search", headers=user_headers,
                       json={"query": "hybrid search", "collection": "b"}).json()["hits"]
    assert hits and all(h["metadata"]["visibility"] == "private" for h in hits)


def test_patch_validation_and_permissions(client, admin_headers, user_headers):
    doc_id = _upload(client, admin_headers).json()["doc_id"]
    assert client.patch(f"/documents/{doc_id}", headers=admin_headers, json={}).status_code == 400
    assert client.patch(f"/documents/{doc_id}", headers=user_headers,
                        json={"title": "x"}).status_code == 403
    assert client.patch(f"/documents/{doc_id}", headers=admin_headers,
                        json={"collection": "bad name"}).status_code == 422
