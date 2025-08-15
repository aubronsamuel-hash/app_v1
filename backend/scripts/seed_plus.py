#!/usr/bin/env python3
"""Seed demo data via API.

Usage:
  python backend/scripts/seed_plus.py --reset --users 10 --missions 6 --days 14 --force-insert
"""
import argparse
import os
from datetime import datetime, timedelta

import httpx

from app.storage import load_db, save_db


def _ensure_admin(base_url: str) -> None:
    """Ensure an admin user (admin/admin) exists in storage."""
    db = load_db()
    users = db.get("users", [])
    admin = next((u for u in users if u.get("username") == "admin"), None)
    if not admin:
        with httpx.Client(base_url=base_url) as client:
            client.post("/auth/register", json={"username": "admin", "password": "admin"})
        db = load_db()
        users = db.get("users", [])
        admin = next((u for u in users if u.get("username") == "admin"), None)
    if admin and admin.get("role") != "admin":
        admin["role"] = "admin"
        save_db(db)


def _login_admin(base_url: str) -> str:
    r = httpx.post(f"{base_url}/auth/token-json", json={"username": "admin", "password": "admin"})
    r.raise_for_status()
    return r.json()["access_token"]


def _reset(base_url: str, token: str) -> None:
    httpx.post(
        f"{base_url}/admin/reset",
        headers={"Authorization": f"Bearer {token}"},
    ).raise_for_status()


def _create_users(client: httpx.Client, token: str, n: int, force: bool) -> list[int]:
    ids: list[int] = []
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(1, n + 1):
        username = f"user{i}"
        if force:
            r = client.get("/admin/users", params={"q": username}, headers=headers)
            if r.status_code == 200:
                items = r.json().get("items", [])
                for it in items:
                    uid = it["id"]
                    client.delete(f"/admin/users/{uid}", headers=headers)
        r = client.post("/auth/register", json={"username": username, "password": "pw"})
        if r.status_code == 409:
            if not force:
                r2 = client.get("/admin/users", params={"q": username}, headers=headers)
                if r2.status_code == 200 and r2.json().get("items"):
                    ids.append(r2.json()["items"][0]["id"])
                continue
            else:
                continue
        r.raise_for_status()
        ids.append(r.json()["id"])
    return ids


def _create_missions(client: httpx.Client, token: str, m: int, d: int, user_ids: list[int]) -> list[int]:
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.utcnow()
    mids: list[int] = []
    for i in range(m):
        start = now + timedelta(days=i % max(1, d))
        end = start + timedelta(hours=2)
        payload = {
            "title": f"Mission {i + 1}",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "status": "published",
            "positions": [
                {"label": "general", "count": max(2, len(user_ids))}
            ],
        }
        r = client.post("/missions", json=payload, headers=headers)
        if r.status_code >= 400:
            continue
        mids.append(r.json()["id"])
    return mids


def _create_assignments(client: httpx.Client, token: str, missions: list[int], user_ids: list[int]) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    for mid in missions:
        for uid in user_ids[:2]:
            payload = {"role_label": "general", "user_id": uid, "status": "invited"}
            client.post(f"/missions/{mid}/assign", json=payload, headers=headers)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data via API")
    parser.add_argument("--reset", action="store_true", help="reset storage before seeding")
    parser.add_argument("--users", type=int, default=5, help="number of users to create")
    parser.add_argument("--missions", type=int, default=3, help="number of missions to create")
    parser.add_argument("--days", type=int, default=7, help="spread missions across D days")
    parser.add_argument("--force-insert", action="store_true", help="remove existing entries before insert")
    args = parser.parse_args()

    base_url = os.environ.get("BASE_URL", "http://localhost:8001").rstrip("/")

    _ensure_admin(base_url)
    token = _login_admin(base_url)
    if args.reset:
        _reset(base_url, token)
        _ensure_admin(base_url)
        token = _login_admin(base_url)

    with httpx.Client(base_url=base_url) as client:
        user_ids = _create_users(client, token, args.users, args.force_insert)
        missions = _create_missions(client, token, args.missions, args.days, user_ids)
        _create_assignments(client, token, missions, user_ids)


if __name__ == "__main__":
    main()
