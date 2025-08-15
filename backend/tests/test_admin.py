import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app
from app.storage import load_db, save_db


def _admin_token(c: TestClient) -> str:
    c.post("/auth/register", json={"username": "admin", "password": "pw"})
    db = load_db()
    db["users"][0]["role"] = "admin"
    save_db(db)
    r = c.post("/auth/token-json", json={"username": "admin", "password": "pw"})
    return r.json()["access_token"]


def test_admin_list_get_put_delete_ok_as_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _admin_token(c)
    H = {"Authorization": f"Bearer {tok}"}
    c.post("/auth/register", json={"username": "u1", "password": "p"})
    c.post("/auth/register", json={"username": "u2", "password": "p"})
    db = load_db()
    uid = next(u["id"] for u in db["users"] if u["username"] == "u1")

    r = c.get("/admin/users", headers=H)
    assert r.status_code == 200
    total = r.json()["total"]
    assert any(u["username"] == "u1" for u in r.json()["items"])

    r = c.get(f"/admin/users/{uid}", headers=H)
    assert r.status_code == 200
    assert r.json()["username"] == "u1"

    r = c.put(f"/admin/users/{uid}", json={"role": "admin", "is_active": False}, headers=H)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert r.json()["is_active"] is False

    r = c.delete(f"/admin/users/{uid}", headers=H)
    assert r.status_code == 204

    r = c.get(f"/admin/users/{uid}", headers=H)
    assert r.status_code == 404

    r = c.get("/admin/users", headers=H)
    assert r.json()["total"] == total - 1

    db = load_db()
    du = next(u for u in db["users"] if u["id"] == uid)
    assert du["is_active"] is False and du.get("deleted_at")

    r = c.post("/admin/reset", headers=H)
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert load_db() == {"users": [], "tokens": [], "missions": [], "assignments": []}


def test_non_admin_forbidden(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    c.post("/auth/register", json={"username": "u", "password": "p"})
    r = c.post("/auth/token-json", json={"username": "u", "password": "p"})
    tok = r.json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    r = c.get("/admin/users", headers=H)
    assert r.status_code == 403
