from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.storage import load_db, save_db
from app.schemas import MissionCreate, MissionUpdate, MissionOut
from app.routers.auth import _current_user as current_user_dep  # reuse auth dep for protected writes

router = APIRouter()


def _ensure_missions(db: Dict[str, Any]) -> None:
    db.setdefault("missions", [])


def _next_id(items: List[Dict[str, Any]]) -> int:
    return (max((x.get("id", 0) for x in items), default=0) + 1)


def _to_out(m: Dict[str, Any]) -> MissionOut:
    # Pydantic will coerce types
    return MissionOut(**m)


@router.get("/missions")
def list_missions(
    q: Optional[str] = None,
    status: Optional[str] = Query(None, pattern="^(draft|published)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    db = load_db()
    _ensure_missions(db)
    items = db["missions"]

    def match(m: Dict[str, Any]) -> bool:
        ok = True
        if q:
            qq = q.lower()
            txt = (m.get("title", "") + " " + (m.get("location") or "")).lower()
            ok = ok and (qq in txt)
        if status:
            ok = ok and (m.get("status") == status)
        if date_from:
            try:
                ok = ok and (datetime.fromisoformat(m["start"]) >= date_from)
            except Exception:
                ok = False
        if date_to:
            try:
                ok = ok and (datetime.fromisoformat(m["end"]) <= date_to)
            except Exception:
                ok = False
        return ok

    filtered = [m for m in items if match(m)]
    filtered.sort(key=lambda m: m.get("start"))  # ISO strings sort well but keep simple

    total = len(filtered)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    slice_items = filtered[start_idx:end_idx]

    return {
        "items": [_to_out(m).model_dump() for m in slice_items],
        "page": page,
        "per_page": per_page,
        "total": total,
    }


@router.post("/missions", response_model=MissionOut)
def create_mission(payload: MissionCreate, user=Depends(current_user_dep)):
    db = load_db()
    _ensure_missions(db)
    # Validate final times (MissionCreate already validates, but explicit check is fine)
    if payload.end <= payload.start:
        raise HTTPException(status_code=422, detail="end must be after start")
    mid = _next_id(db["missions"])
    m = payload.model_dump()
    m["id"] = mid
    # Serialize datetimes to isoformat
    m["start"] = payload.start.isoformat()
    m["end"] = payload.end.isoformat()
    db["missions"].append(m)
    save_db(db)
    return _to_out(m)


@router.get("/missions/{mid}", response_model=MissionOut)
def get_mission(mid: int):
    db = load_db()
    _ensure_missions(db)
    m = next((x for x in db["missions"] if x.get("id") == mid), None)
    if not m:
        raise HTTPException(status_code=404, detail="mission not found")
    return _to_out(m)


@router.put("/missions/{mid}", response_model=MissionOut)
def update_mission(mid: int, payload: MissionUpdate, user=Depends(current_user_dep)):
    db = load_db()
    _ensure_missions(db)
    idx = next((i for i, x in enumerate(db["missions"]) if x.get("id") == mid), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="mission not found")
    cur = dict(db["missions"][idx])

    # Apply updates
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k in ("start", "end") and v is not None and hasattr(v, "isoformat"):
            data[k] = v.isoformat()
    cur.update(data)

    # Re-validate combined times if both present (or after update)
    try:
        s = cur.get("start")
        e = cur.get("end")
        if s and e and datetime.fromisoformat(e) <= datetime.fromisoformat(s):
            raise HTTPException(status_code=422, detail="end must be after start")
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid datetime format")

    db["missions"][idx] = cur
    save_db(db)
    return _to_out(cur)


@router.delete("/missions/{mid}", status_code=204)
def delete_mission(mid: int, user=Depends(current_user_dep)):
    db = load_db()
    _ensure_missions(db)
    before = len(db["missions"])
    db["missions"] = [x for x in db["missions"] if x.get("id") != mid]
    if len(db["missions"]) == before:
        raise HTTPException(status_code=404, detail="mission not found")
    save_db(db)
    return

