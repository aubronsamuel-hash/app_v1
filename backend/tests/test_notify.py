import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app
from app.storage import load_db, save_db


def _token(c: TestClient, username: str, password: str) -> str:
    c.post("/auth/register", json={"username": username, "password": password})
    r = c.post("/auth/token-json", json={"username": username, "password": password})
    return r.json()["access_token"]


def _admin_token(c: TestClient) -> str:
    tok = _token(c, "admin", "pw")
    db = load_db()
    db["users"][0]["role"] = "admin"
    save_db(db)
    return tok


def test_prefs_update_and_notify_test_dry_run(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NOTIFY_DRY_RUN", "1")
    c = TestClient(app)
    tok = _token(c, "u", "p")
    H = {"Authorization": f"Bearer {tok}"}
    r = c.put(
        "/auth/me/prefs",
        headers=H,
        json={"email": "u@example.com", "telegram": True, "telegram_chat_id": "123"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "u@example.com"
    db = load_db()
    prefs = next(u for u in db["users"] if u["username"] == "u")["prefs"]
    assert prefs["telegram"] is True
    r = c.post("/auth/me/notify-test", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is True
    assert set(body["channels"]) == {"email", "telegram"}


def test_admin_diag_requires_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NOTIFY_DRY_RUN", "1")
    c = TestClient(app)
    admin_tok = _admin_token(c)
    user_tok = _token(c, "user", "pw")
    H_user = {"Authorization": f"Bearer {user_tok}"}
    H_admin = {"Authorization": f"Bearer {admin_tok}"}
    c.put("/auth/me/prefs", headers=H_user, json={"email": "user@example.com"})
    r = c.get("/admin/notifications/diagnostic", headers=H_user)
    assert r.status_code == 403
    r = c.post("/admin/notifications/diagnostic/test", headers=H_user)
    assert r.status_code == 403
    r = c.get("/admin/notifications/diagnostic", headers=H_admin)
    assert r.status_code == 200
    assert r.json()["users_with_prefs"] == 1
    r = c.post("/admin/notifications/diagnostic/test", headers=H_admin)
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is True and body["tested"] == 1
