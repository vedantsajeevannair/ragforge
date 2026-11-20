def test_first_user_is_admin_then_users(client, admin_headers, user_headers):
    assert client.get("/auth/me", headers=admin_headers).json()["role"] == "admin"
    assert client.get("/auth/me", headers=user_headers).json()["role"] == "user"


def test_duplicate_username_conflicts(client, admin_headers):
    resp = client.post("/auth/register", json={"username": "admin", "password": "password123"})
    assert resp.status_code == 409


def test_login_success_and_failure(client, admin_headers):
    ok = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    assert ok.status_code == 200 and ok.json()["role"] == "admin"
    bad = client.post("/auth/login", json={"username": "admin", "password": "wrongpass1"})
    assert bad.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    bad = client.get("/auth/me", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401


def test_register_validates_input(client):
    assert client.post("/auth/register", json={"username": "a", "password": "x"}).status_code == 422
