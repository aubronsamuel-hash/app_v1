import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app

def test_register_login_me_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)

    r = c.post("/auth/register", json={"username":"admin","password":"admin"})
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "admin"

    r = c.post("/auth/token-json", json={"username":"admin","password":"admin"})
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    assert tok.startswith("tok_")

    r = c.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["username"] == "admin"

def test_register_duplicate_409(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    c.post("/auth/register", json={"username":"u","password":"p"})
    r = c.post("/auth/register", json={"username":"u","password":"p"})
    assert r.status_code == 409

def test_me_401_without_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = TestClient(app)
    r = c.get("/auth/me")
    assert r.status_code == 401
