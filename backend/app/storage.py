import json, os, threading
from typing import Any, Dict

_lock = threading.Lock()

def _data_dir() -> str:
    d = os.environ.get("DATA_DIR", "/data")
    os.makedirs(d, exist_ok=True)
    return d

def _db_path() -> str:
    return os.path.join(_data_dir(), "data.json")

def _init_if_missing(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"users": [], "tokens": [], "missions": [], "assignments": []}, f)

def load_db() -> Dict[str, Any]:
    path = _db_path()
    _init_if_missing(path)
    with _lock:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

def save_db(db: Dict[str, Any]) -> None:
    path = _db_path()
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=True, indent=2)
