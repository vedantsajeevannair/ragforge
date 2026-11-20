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
