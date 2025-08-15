import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app


def _token(c: TestClient) -> str:
    c.post("/auth/register", json={"username": "u", "password": "p"})
    r = c.post("/auth/token-json", json={"username": "u", "password": "p"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _mission(c: TestClient, headers):
    body = {
        "title": "Show A",
        "start": "2025-08-16T08:00:00+04:00",
        "end": "2025-08-16T12:00:00+04:00",
        "status": "draft",
        "positions": [{"label": "SON", "count": 1, "skills": {}}],
    }
    r = c.post("/missions", json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_assign_ok_then_capacity_exceeded_422(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _token(c)
    H = {"Authorization": f"Bearer {tok}"}
    mid = _mission(c, H)

    r = c.post(f"/missions/{mid}/assign", json={"role_label": "SON", "user_id": 1}, headers=H)
    assert r.status_code == 200, r.text

    r = c.post(f"/missions/{mid}/assign", json={"role_label": "SON", "user_id": 2}, headers=H)
    assert r.status_code == 422


def test_assign_invalid_role_422(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _token(c)
    H = {"Authorization": f"Bearer {tok}"}
    mid = _mission(c, H)

    r = c.post(f"/missions/{mid}/assign", json={"role_label": "DRUM", "user_id": 1}, headers=H)
    assert r.status_code == 422


def test_delete_assignment_204_and_404(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _token(c)
    H = {"Authorization": f"Bearer {tok}"}
    mid = _mission(c, H)

    r = c.post(f"/missions/{mid}/assign", json={"role_label": "SON", "user_id": 1}, headers=H)
    assert r.status_code == 200, r.text
    aid = r.json()["id"]

    r = c.delete(f"/missions/{mid}/assignments/{aid}", headers=H)
    assert r.status_code == 204

    r = c.delete(f"/missions/{mid}/assignments/{aid}", headers=H)
    assert r.status_code == 404
