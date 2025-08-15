from __future__ import annotations

from pathlib import Path

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.main import app

DB_PATH = Path("/data/data.json")


@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_register_login_me_ok():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/auth/register", json={"username": "alice", "password": "secret"})
            assert res.status_code == 200
            assert res.json() == {"id": 1, "username": "alice", "role": "intermittent"}

            res = await ac.post("/auth/token-json", json={"username": "alice", "password": "secret"})
            assert res.status_code == 200
            token = res.json()["access_token"]

            res = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            assert res.json() == {"id": 1, "username": "alice", "role": "intermittent"}
    asyncio.run(_run())


def test_register_duplicate_409():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r1 = await ac.post("/auth/register", json={"username": "bob", "password": "pw"})
            assert r1.status_code == 200
            r2 = await ac.post("/auth/register", json={"username": "bob", "password": "pw"})
            assert r2.status_code == 409
            assert r2.json()["detail"] == "nom d'utilisateur deja pris"
    asyncio.run(_run())


def test_me_401_without_token():
    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/auth/me")
            assert res.status_code == 401
            assert res.json()["detail"] == "token invalide"
    asyncio.run(_run())
