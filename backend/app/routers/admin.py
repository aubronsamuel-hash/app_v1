from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.storage import load_db, save_db
from app.schemas import UserOut, UserAdminUpdate
from app.routers.auth import _current_user as current_user_dep
import os

router = APIRouter()


def _admin_user(user: Dict[str, Any] = Depends(current_user_dep)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return user


def _to_out(u: Dict[str, Any]) -> UserOut:
    return UserOut(
        id=u["id"],
        username=u["username"],
        role=u.get("role", "intermittent"),
        is_active=u.get("is_active", True),
    )


@router.get("/admin/users")
def list_users(
    q: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    user: Dict[str, Any] = Depends(_admin_user),
):
    db = load_db()
    users = [u for u in db.get("users", []) if not u.get("deleted_at")]
    if q:
        ql = q.lower()
        users = [u for u in users if ql in u.get("username", "").lower()]
    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    items = [_to_out(u).model_dump() for u in users[start:end]]
    return {"items": items, "page": page, "per_page": per_page, "total": total}


@router.get("/admin/users/{uid}", response_model=UserOut)
def get_user(uid: int, user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    u = next((u for u in db.get("users", []) if u.get("id") == uid and not u.get("deleted_at")), None)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    return _to_out(u)


@router.put("/admin/users/{uid}", response_model=UserOut)
def update_user(uid: int, payload: UserAdminUpdate, user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    users = db.get("users", [])
    idx = next((i for i, u in enumerate(users) if u.get("id") == uid and not u.get("deleted_at")), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="user not found")
    cur = dict(users[idx])
    if payload.role is not None:
        cur["role"] = payload.role
    if payload.is_active is not None:
        cur["is_active"] = payload.is_active
    users[idx] = cur
    save_db(db)
    return _to_out(cur)


@router.delete("/admin/users/{uid}", status_code=204)
def delete_user(uid: int, user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    u = next((u for u in db.get("users", []) if u.get("id") == uid and not u.get("deleted_at")), None)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    u["deleted_at"] = datetime.now(timezone.utc).isoformat()
    u["is_active"] = False
    save_db(db)
    return


@router.post("/admin/reset")
def reset(user: Dict[str, Any] = Depends(_admin_user)):
    db = {"users": [], "tokens": [], "missions": [], "assignments": []}
    save_db(db)
    return {"ok": True}


def _users_with_prefs(db: Dict[str, Any]):
    def has_prefs(u: Dict[str, Any]) -> bool:
        prefs = u.get("prefs", {})
        return any(prefs.get(k) for k in ["email", "telegram", "telegram_chat_id"])
    return [u for u in db.get("users", []) if has_prefs(u)]


@router.get("/admin/notifications/diagnostic")
def notifications_diag(user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    users = _users_with_prefs(db)
    return {"users_with_prefs": len(users)}


@router.post("/admin/notifications/diagnostic/test")
def notifications_diag_test(user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    users = _users_with_prefs(db)
    dry_run = os.environ.get("NOTIFY_DRY_RUN", "1") == "1"
    tested = 0
    for u in users:
        prefs = u.get("prefs", {})
        channels = []
        if prefs.get("email"):
            channels.append("email")
        if prefs.get("telegram") and prefs.get("telegram_chat_id"):
            channels.append("telegram")
        tested += 1
        if dry_run:
            for ch in channels:
                if ch == "email":
                    print(f"DRY RUN: would send email to {prefs.get('email')}")
                elif ch == "telegram":
                    print(f"DRY RUN: would send telegram to {prefs.get('telegram_chat_id')}")
    return {"ok": True, "dry_run": dry_run, "tested": tested}

