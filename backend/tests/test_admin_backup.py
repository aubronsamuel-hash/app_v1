import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app
from app.storage import load_db, save_db


def _admin_token(c: TestClient) -> str:
    c.post("/auth/register", json={"username": "admin", "password": "pw"})
    db = load_db()
    admin = next(u for u in db["users"] if u["username"] == "admin")
    admin["role"] = "admin"
    save_db(db)
    r = c.post("/auth/token-json", json={"username": "admin", "password": "pw"})
    return r.json()["access_token"]


def test_backup_contains_keys_admin_only(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    c.post("/auth/register", json={"username": "u", "password": "p"})
    r = c.post("/auth/token-json", json={"username": "u", "password": "p"})
    tok = r.json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    r = c.get("/admin/backup", headers=H)
    assert r.status_code == 403
    tok = _admin_token(c)
    H = {"Authorization": f"Bearer {tok}"}
    r = c.get("/admin/backup", headers=H)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "attachment; filename=\"backup_" in r.headers.get("content-disposition", "")
    data = r.json()
    assert data["version"] == 1
    assert set(data["payload"].keys()) == {"users", "tokens", "missions", "assignments"}


def test_restore_wipe_roundtrip_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _admin_token(c)
    H = {"Authorization": f"Bearer {tok}"}
    c.post("/auth/register", json={"username": "u1", "password": "p"})
    c.post("/auth/register", json={"username": "u2", "password": "p"})
    c.post("/auth/token-json", json={"username": "u1", "password": "p"})
    c.post("/auth/token-json", json={"username": "u2", "password": "p"})
    mission = {
        "title": "m1",
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-02T00:00:00Z",
        "positions": [{"label": "r1", "count": 1, "skills": {}}],
    }
    r = c.post("/missions", json=mission, headers=H)
    mid = r.json()["id"]
    db = load_db()
    uid1 = next(u["id"] for u in db["users"] if u["username"] == "u1")
    c.post(f"/missions/{mid}/assign", json={"role_label": "r1", "user_id": uid1, "status": "invited"}, headers=H)
    r = c.get("/admin/backup", headers=H)
    backup = r.json()
    counts = {k: len(backup["payload"][k]) for k in ["users", "tokens", "missions", "assignments"]}
    c.post("/admin/reset", headers=H)
    tok = _admin_token(c)
    H = {"Authorization": f"Bearer {tok}"}
    r = c.post("/admin/restore", json=backup, headers=H)
    assert r.status_code == 200
    db2 = load_db()
    for k, v in counts.items():
        assert len(db2.get(k, [])) == v


def test_restore_merge_nowipe_upserts_without_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    tok = _admin_token(c)
    H = {"Authorization": f"Bearer {tok}"}
    mission = {
        "title": "orig",
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-02T00:00:00Z",
        "positions": [{"label": "r1", "count": 1, "skills": {}}],
    }
    r = c.post("/missions", json=mission, headers=H)
    mid1 = r.json()["id"]
    db = load_db()
    admin_id = next(u["id"] for u in db["users"] if u["username"] == "admin")
    c.post(f"/missions/{mid1}/assign", json={"role_label": "r1", "user_id": admin_id, "status": "invited"}, headers=H)
    orig_tokens = load_db().get("tokens", []).copy()
    r = c.get("/admin/backup", headers=H)
    backup = r.json()
    backup["payload"]["users"][0]["username"] = "admin2"
    backup["payload"]["users"].append({
        "id": 2,
        "username": "bob",
        "password_hash": "x",
        "role": "intermittent",
        "is_active": True,
    })
    backup["payload"]["tokens"] = [{"token": "bad", "user_id": 2, "created_at": "2020-01-01T00:00:00Z"}]
    backup["payload"]["missions"][0]["title"] = "changed"
    backup["payload"]["missions"].append({
        "id": 2,
        "title": "m2",
        "start": "2025-01-03T00:00:00Z",
        "end": "2025-01-04T00:00:00Z",
        "status": "draft",
        "positions": [{"label": "r1", "count": 1, "skills": {}}],
    })
    backup["payload"]["assignments"][0]["status"] = "confirmed"
    backup["payload"]["assignments"].append({
        "id": 2,
        "mission_id": 2,
        "user_id": 2,
        "role_label": "r1",
        "status": "invited",
    })
    r = c.post("/admin/restore?wipe=false", json=backup, headers=H)
    assert r.status_code == 200
    db2 = load_db()
    u1 = next(u for u in db2["users"] if u["id"] == 1)
    assert u1["username"] == "admin2"
    assert any(u["id"] == 2 for u in db2["users"])
    m1 = next(m for m in db2["missions"] if m["id"] == mid1)
    assert m1["title"] == "changed"
    assert any(m["id"] == 2 for m in db2["missions"])
    a1 = next(a for a in db2["assignments"] if a["id"] == 1)
    assert a1["status"] == "confirmed"
    assert any(a["id"] == 2 for a in db2["assignments"])
    assert db2.get("tokens", []) == orig_tokens
