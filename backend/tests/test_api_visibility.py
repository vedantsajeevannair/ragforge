import pytest

SECRET = b"The launch code for project falcon is purple-elephant."


@pytest.fixture
def private_doc(client, user_headers):
    resp = client.post("/documents", headers=user_headers,
                       files={"file": ("falcon.txt", SECRET)}, data={"visibility": "private"})
    assert resp.status_code == 201 and resp.json()["visibility"] == "private"
    return resp.json()["doc_id"]


@pytest.fixture
def carol(client, admin_headers):
    r = client.post("/auth/register", json={"username": "carol", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_private_document_hidden_from_other_users(client, private_doc, carol):
    assert client.get("/documents", headers=carol).json() == []
    assert client.get("/documents", headers=carol).headers["x-total-count"] == "0"
    for path in ("", "/chunks", "/download"):
        assert client.get(f"/documents/{private_doc}{path}", headers=carol).status_code == 404
    hits = client.post("/search", headers=carol, json={"query": "falcon launch code"}).json()
    assert hits["hits"] == []
    ans = client.post("/ask", headers=carol, json={"query": "falcon launch code"}).json()
    assert "purple" not in ans["answer"]


def test_owner_and_admin_can_see_private_document(client, private_doc, user_headers,
                                                  admin_headers):
    for headers in (user_headers, admin_headers):
        assert [d["doc_id"] for d in client.get("/documents", headers=headers).json()] \
            == [private_doc]
        hits = client.post("/search", headers=headers, json={"query": "falcon"}).json()["hits"]
        assert hits and hits[0]["doc_id"] == private_doc


def test_other_user_cannot_delete_private_document(client, private_doc, carol):
    assert client.delete(f"/documents/{private_doc}", headers=carol).status_code == 404
