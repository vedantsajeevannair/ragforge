from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    settings = Settings(jwt_secret="test-secret-" + "x" * 32, embedding_dim=256)
    with TestClient(create_app(settings, in_memory=True)) as c:
        yield c


def _register(client, username, password="password123"):
    resp = client.post("/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return _register(client, "admin")


@pytest.fixture
def user_headers(client, admin_headers):
    return _register(client, "bob")
