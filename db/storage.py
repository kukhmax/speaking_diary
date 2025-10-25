from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

DEFAULT_DB_PATH = Path("data/diary.sqlite")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Initialize SQLite DB with minimal schema and return normalized Path.

    Schema: entries(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, text TEXT)
    """
    p = Path(db_path)
    _ensure_parent(p)
    with sqlite3.connect(p) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                text TEXT NOT NULL
            )
            """
        )
        conn.commit()
    return p


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def add_entry(db_path: str | Path, created_at: datetime | str, text: str) -> int:
    if isinstance(created_at, datetime):
        created = created_at.replace(microsecond=0).isoformat()
    else:
        created = str(created_at)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO entries (created_at, text) VALUES (?, ?)",
            (created, text),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_entries(db_path: str | Path, limit: int = 100) -> List[Dict[str, str]]:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, created_at, text FROM entries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [{k: row[k] for k in row.keys()} for row in rows]


def get_entry(db_path: str | Path, entry_id: int) -> Optional[Dict[str, str]]:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, created_at, text FROM entries WHERE id = ?",
            (entry_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {k: row[k] for k in row.keys()}