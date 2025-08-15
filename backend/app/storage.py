from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

DB_PATH = Path("/data/data.json")


def _ensure_db_file() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        with DB_PATH.open("w", encoding="utf-8") as f:
            json.dump({"users": [], "tokens": []}, f)


def load_db() -> Dict[str, Any]:
    """Load database from JSON file, creating it if missing."""
    _ensure_db_file()
    with DB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db: Dict[str, Any]) -> None:
    """Persist database to JSON file."""
    _ensure_db_file()
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(db, f)
