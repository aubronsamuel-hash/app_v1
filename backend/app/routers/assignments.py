from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from app.storage import load_db, save_db
from app.schemas import AssignmentIn, AssignmentOut
from app.routers.auth import _current_user as current_user_dep

router = APIRouter()


def _ensure_missions(db: Dict[str, Any]) -> None:
    db.setdefault("missions", [])


def _ensure_assignments(db: Dict[str, Any]) -> None:
    db.setdefault("assignments", [])


def _next_id(items: List[Dict[str, Any]]) -> int:
    return (max((x.get("id", 0) for x in items), default=0) + 1)


def _to_out(a: Dict[str, Any]) -> AssignmentOut:
    return AssignmentOut(**a)


@router.post("/missions/{mid}/assign", response_model=AssignmentOut)
def create_assignment(mid: int, payload: AssignmentIn, user=Depends(current_user_dep)):
    db = load_db()
    _ensure_missions(db)
    _ensure_assignments(db)
    mission = next((m for m in db["missions"] if m.get("id") == mid), None)
    if not mission:
        raise HTTPException(status_code=404, detail="mission not found")
    pos = next((p for p in mission.get("positions", []) if p.get("label") == payload.role_label), None)
    if not pos:
        raise HTTPException(status_code=422, detail="invalid role_label")
    existing = [
        a for a in db["assignments"]
        if a.get("mission_id") == mid and a.get("role_label") == payload.role_label
    ]
    if len(existing) >= pos.get("count", 0):
        raise HTTPException(status_code=422, detail="capacity exceeded")
    aid = _next_id(db["assignments"])
    a = {
        "id": aid,
        "mission_id": mid,
        "user_id": payload.user_id,
        "role_label": payload.role_label,
        "status": payload.status,
    }
    db["assignments"].append(a)
    save_db(db)
    return _to_out(a)


@router.get("/missions/{mid}/assignments")
def list_assignments(mid: int):
    db = load_db()
    _ensure_missions(db)
    _ensure_assignments(db)
    mission = next((m for m in db["missions"] if m.get("id") == mid), None)
    if not mission:
        raise HTTPException(status_code=404, detail="mission not found")
    items = [
        _to_out(a).model_dump() for a in db["assignments"] if a.get("mission_id") == mid
    ]
    return {"items": items, "total": len(items)}


@router.delete("/missions/{mid}/assignments/{aid}", status_code=204)
def delete_assignment(mid: int, aid: int, user=Depends(current_user_dep)):
    db = load_db()
    _ensure_missions(db)
    _ensure_assignments(db)
    mission = next((m for m in db["missions"] if m.get("id") == mid), None)
    if not mission:
        raise HTTPException(status_code=404, detail="mission not found")
    idx = next(
        (
            i
            for i, a in enumerate(db["assignments"])
            if a.get("id") == aid and a.get("mission_id") == mid
        ),
        None,
    )
    if idx is None:
        raise HTTPException(status_code=404, detail="assignment not found")
    db["assignments"].pop(idx)
    save_db(db)
    return
