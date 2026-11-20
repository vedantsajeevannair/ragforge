def _me(client, headers):
    return client.get("/auth/me", headers=headers).json()


def test_admin_lists_and_promotes_users(client, admin_headers, user_headers):
    users = client.get("/users", headers=admin_headers).json()
    assert [u["username"] for u in users] == ["admin", "bob"]
    bob = _me(client, user_headers)["id"]
    resp = client.patch(f"/users/{bob}", headers=admin_headers, json={"role": "admin"})
    assert resp.json()["role"] == "admin"


def test_regular_user_cannot_manage_users(client, user_headers):
    assert client.get("/users", headers=user_headers).status_code == 403


def test_last_admin_is_protected(client, admin_headers):
    admin_id = _me(client, admin_headers)["id"]
    demote = client.patch(f"/users/{admin_id}", headers=admin_headers, json={"role": "user"})
    assert demote.status_code == 409
    assert client.delete(f"/users/{admin_id}", headers=admin_headers).status_code == 409


def test_delete_user(client, admin_headers, user_headers):
    bob = _me(client, user_headers)["id"]
    assert client.delete(f"/users/{bob}", headers=admin_headers).status_code == 204
    assert client.get("/auth/me", headers=user_headers).status_code == 401
    assert client.delete(f"/users/{bob}", headers=admin_headers).status_code == 404


def test_change_password(client, user_headers):
    bad = client.post("/auth/password", headers=user_headers,
                      json={"current_password": "nope", "new_password": "newpassword1"})
    assert bad.status_code == 400
    ok = client.post("/auth/password", headers=user_headers,
                     json={"current_password": "password123", "new_password": "newpassword1"})
    assert ok.status_code == 204
    login = client.post("/auth/login", json={"username": "bob", "password": "newpassword1"})
    assert login.status_code == 200
