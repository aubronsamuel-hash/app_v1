import os, sys, json, importlib
from datetime import datetime, timedelta, timezone
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_token_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TOKEN_TTL", "1")
    from fastapi.testclient import TestClient
    from app import config
    import app.main as main
    importlib.reload(config)
    importlib.reload(main)
    c = TestClient(main.app)
    c.post("/auth/register", json={"username": "u", "password": "p"})
    r = c.post("/auth/token-json", json={"username": "u", "password": "p"})
    tok = r.json()["access_token"]
    db_path = tmp_path / "data.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    old = datetime.now(timezone.utc) - timedelta(minutes=2)
    db["tokens"][0]["created_at"] = old.isoformat()
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=True, indent=2)
    r = c.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expired"
