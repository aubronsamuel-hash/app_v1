import os, sys, importlib
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_cors_origins_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    from fastapi.testclient import TestClient
    from app import config
    import app.main as main
    importlib.reload(config)
    importlib.reload(main)
    c = TestClient(main.app)
    r = c.get("/healthz", headers={"Origin": "http://example.com"})
    assert r.headers["access-control-allow-origin"] == "http://example.com"
