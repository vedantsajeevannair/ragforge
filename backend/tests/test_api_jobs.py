from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client():
    settings = Settings(jwt_secret="j" * 40, embedding_dim=64, async_upload_kb=1)
    return TestClient(create_app(settings, in_memory=True))


def _login(c, name):
    r = c.post("/auth/register", json={"username": name, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_large_upload_runs_as_background_job():
    with _client() as c:
        h = _login(c, "ann")
        big = ("Background indexing keeps uploads responsive. " * 40).encode()
        resp = c.post("/documents", headers=h, files={"file": ("big.txt", big)})
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        c.app.state.ragforge.jobs.join()
        job = c.get(f"/jobs/{job_id}", headers=h).json()
        assert job["status"] == "done"
        assert job["result"]["filename"] == "big.txt"
        assert c.get("/documents", headers=h).json()[0]["doc_id"] == job["result"]["doc_id"]


def test_failed_job_reports_clean_error_and_is_private():
    with _client() as c:
        h = _login(c, "ann")
        other = _login(c, "ben")
        empty_csv = b"col\n" + b" \n" * 1100
        resp = c.post("/documents", headers=h, files={"file": ("e.csv", empty_csv)})
        job_id = resp.json()["job_id"]
        c.app.state.ragforge.jobs.join()
        job = c.get(f"/jobs/{job_id}", headers=h).json()
        assert job["status"] == "failed"
        assert job["error"] == "no extractable text found"
        assert c.get(f"/jobs/{job_id}", headers=other).status_code == 404


def test_small_upload_stays_synchronous():
    with _client() as c:
        h = _login(c, "ann")
        assert c.post("/documents", headers=h, files={"file": ("s.txt", b"tiny")}).status_code == 201
