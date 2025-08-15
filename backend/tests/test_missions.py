import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))
from fastapi.testclient import TestClient
from app.main import app


def _token(c: TestClient) -> str:
    c.post("/auth/register", json={"username": "u", "password": "p"})
    r = c.post("/auth/token-json", json={"username": "u", "password": "p"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_create_list_update_delete_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _token(c)
    H = {"Authorization": f"Bearer {tok}"}

    body = {
        "title": "Show A",
        "start": "2025-08-16T08:00:00+04:00",
        "end": "2025-08-16T12:00:00+04:00",
        "status": "draft",
        "positions": [{"label": "SON", "count": 1, "skills": {}}],
    }
    r = c.post("/missions", json=body, headers=H)
    assert r.status_code == 200, r.text
    mid = r.json()["id"]

    r = c.get("/missions")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    # Update
    r = c.put(f"/missions/{mid}", json={"status": "published"}, headers=H)
    assert r.status_code == 200
    assert r.json()["status"] == "published"

    # Delete
    r = c.delete(f"/missions/{mid}", headers=H)
    assert r.status_code == 204

    # Not found after delete
    r = c.get(f"/missions/{mid}")
    assert r.status_code == 404


def test_create_invalid_dates_422(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _token(c)
    H = {"Authorization": f"Bearer {tok}"}

    body = {
        "title": "Bad",
        "start": "2025-08-16T12:00:00+04:00",
        "end": "2025-08-16T08:00:00+04:00",
        "status": "draft",
        "positions": [],
    }
    r = c.post("/missions", json=body, headers=H)
    assert r.status_code in (400, 422), r.text

