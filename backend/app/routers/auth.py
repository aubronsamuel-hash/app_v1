from __future__ import annotations

from datetime import datetime, timezone
import secrets

import bcrypt
from fastapi import APIRouter, HTTPException, Header

from app.schemas import UserIn, UserOut, TokenOut
from app.storage import load_db, save_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserIn) -> UserOut:
    db = load_db()
    if any(u["username"] == user_in.username for u in db["users"]):
        raise HTTPException(status_code=409, detail="nom d'utilisateur deja pris")
    user_id = max([u["id"] for u in db["users"]] or [0]) + 1
    password_hash = bcrypt.hashpw(user_in.password.encode(), bcrypt.gensalt()).decode()
    user = {
        "id": user_id,
        "username": user_in.username,
        "password_hash": password_hash,
        "role": "intermittent",
        "is_active": True,
    }
    db["users"].append(user)
    save_db(db)
    return UserOut(id=user_id, username=user_in.username, role="intermittent")


@router.post("/token-json", response_model=TokenOut)
def token_json(user_in: UserIn) -> TokenOut:
    db = load_db()
    user = next((u for u in db["users"] if u["username"] == user_in.username), None)
    if not user or not bcrypt.checkpw(user_in.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="identifiants invalides")
    token = f"tok_{user['id']}_{secrets.token_hex(8)}"
    db["tokens"].append({
        "token": token,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    save_db(db)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(authorization: str | None = Header(None)) -> UserOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="token invalide")
    token = authorization.split()[1]
    db = load_db()
    token_entry = next((t for t in db["tokens"] if t["token"] == token), None)
    if not token_entry:
        raise HTTPException(status_code=401, detail="token invalide")
    user = next((u for u in db["users"] if u["id"] == token_entry["user_id"]), None)
    if not user or not user.get("is_active", False):
        raise HTTPException(status_code=401, detail="utilisateur inactif")
    return UserOut(id=user["id"], username=user["username"], role=user["role"])
