from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
from datetime import datetime, timezone
from app.storage import load_db, save_db
from app.routers.auth import _current_user as current_user_dep

router = APIRouter()


def _admin_user(user: Dict[str, Any] = Depends(current_user_dep)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return user


@router.get("/admin/backup")
def backup(user: Dict[str, Any] = Depends(_admin_user)):
    db = load_db()
    payload = {
        "users": db.get("users", []),
        "tokens": db.get("tokens", []),
        "missions": db.get("missions", []),
        "assignments": db.get("assignments", []),
    }
    now = datetime.now(timezone.utc)
    data = {
        "version": 1,
        "created_at": now.isoformat(),
        "payload": payload,
    }
    filename = f"backup_{now.strftime('%Y%m%d_%H%M%S')}.json"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return JSONResponse(content=data, headers=headers)


@router.post("/admin/restore")
def restore(
    data: Dict[str, Any] = Body(...),
    wipe: bool = True,
    user: Dict[str, Any] = Depends(_admin_user),
):
    if data.get("version") != 1 or not isinstance(data.get("payload"), dict):
        raise HTTPException(status_code=422, detail="invalid backup")
    payload = data["payload"]
    required = ["users", "tokens", "missions", "assignments"]
    for k in required:
        if k not in payload or not isinstance(payload.get(k), list):
            raise HTTPException(status_code=422, detail="invalid backup")
    if wipe:
        db = {k: payload.get(k, []) for k in required}
    else:
        db = load_db()
        for k in ["users", "missions", "assignments"]:
            existing = db.get(k, [])
            index = {item.get("id"): i for i, item in enumerate(existing)}
            for item in payload.get(k, []):
                idx = index.get(item.get("id"))
                if idx is None:
                    existing.append(item)
                else:
                    existing[idx] = item
            db[k] = existing
        db.setdefault("tokens", [])
    save_db(db)
    return {"ok": True}
