import os, sys, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app

def test_token_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    c.post("/auth/register", json={"username":"u","password":"p"})
    r = c.post("/auth/token-json", json={"username":"u","password":"p"})
    tok = r.json()["access_token"]
    db_path = tmp_path / "data.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    db["tokens"][0]["created_at"] = "2000-01-01T00:00:00+00:00"
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=True, indent=2)
    r = c.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expired"
