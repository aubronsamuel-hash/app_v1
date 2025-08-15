from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, Dict, Any
from app.storage import load_db, save_db
from app.schemas import UserIn, UserOut, TokenOut, NotificationPrefsIn
import secrets, bcrypt, os
from datetime import datetime, timezone

router = APIRouter()

def _hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def _new_token(user_id: int) -> str:
    return "tok_{0}_{1}".format(user_id, secrets.token_hex(16))

@router.post("/auth/register", response_model=UserOut)
def register(payload: UserIn):
    db = load_db()
    if any(u["username"] == payload.username for u in db.get("users", [])):
        raise HTTPException(status_code=409, detail="User already exists")
    next_id = (max([u.get("id", 0) for u in db.get("users", [])]) + 1) if db.get("users") else 1
    user = {
        "id": next_id,
        "username": payload.username,
        "password_hash": _hash_password(payload.password),
        "role": "intermittent",
        "is_active": True,
    }
    db["users"].append(user)
    save_db(db)
    return {
        "id": next_id,
        "username": payload.username,
        "role": "intermittent",
        "is_active": True,
    }

@router.post("/auth/token-json", response_model=TokenOut)
def token_json(payload: UserIn):
    db = load_db()
    user = next((u for u in db.get("users", []) if u["username"] == payload.username), None)
    if not user or not _verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    tok = _new_token(user["id"])
    db.setdefault("tokens", [])
    db["tokens"] = [t for t in db["tokens"] if t.get("user_id") != user["id"]]
    db["tokens"].append({"token": tok, "user_id": user["id"], "created_at": datetime.now(timezone.utc).isoformat()})
    save_db(db)
    return {"access_token": tok}

def _current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token required")
    token = authorization.split(" ", 1)[1].strip()
    db = load_db()
    t = next((t for t in db.get("tokens", []) if t["token"] == token), None)
    if not t:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = next((u for u in db.get("users", []) if u["id"] == t["user_id"]), None)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Inactive user")
    return user

@router.get("/auth/me", response_model=UserOut)
def me(user: Dict[str, Any] = Depends(_current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user.get("role", "intermittent"),
        "is_active": user.get("is_active", True),
    }


@router.put("/auth/me/prefs")
def update_prefs(payload: NotificationPrefsIn, user: Dict[str, Any] = Depends(_current_user)):
    db = load_db()
    users = db.get("users", [])
    idx = next((i for i, u in enumerate(users) if u.get("id") == user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="user not found")
    prefs = payload.model_dump()
    users[idx]["prefs"] = prefs
    save_db(db)
    return prefs


@router.post("/auth/me/notify-test")
def notify_test(user: Dict[str, Any] = Depends(_current_user)):
    prefs = user.get("prefs", {}) or {}
    channels = []
    if prefs.get("email"):
        channels.append("email")
    if prefs.get("telegram") and prefs.get("telegram_chat_id"):
        channels.append("telegram")
    dry_run = os.environ.get("NOTIFY_DRY_RUN", "1") == "1"
    if dry_run:
        for ch in channels:
            if ch == "email":
                print(f"DRY RUN: would send email to {prefs.get('email')}")
            elif ch == "telegram":
                print(f"DRY RUN: would send telegram to {prefs.get('telegram_chat_id')}")
    return {"ok": True, "dry_run": dry_run, "channels": channels}
