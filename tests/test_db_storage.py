from pathlib import Path
from datetime import datetime, timedelta

from db.storage import init_db, add_entry, list_entries, get_entry


def test_init_db_creates_file_and_table(tmp_path: Path):
    db_path = tmp_path / "data" / "diary.sqlite"
    # init
    p = init_db(db_path)
    assert p.exists(), "DB file should be created"

    # verify table exists via sqlite_master
    import sqlite3
    with sqlite3.connect(p) as conn:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        assert cur.fetchone() is not None, "entries table must exist"


def test_add_and_list_entries(tmp_path: Path):
    db = init_db(tmp_path / "diary.sqlite")
    user = "u1"
    now = datetime.utcnow().replace(microsecond=0)

    id1 = add_entry(db, user, now - timedelta(minutes=2), "first")
    id2 = add_entry(db, user, now - timedelta(minutes=1), "second")
    id3 = add_entry(db, user, now, "third")

    assert id1 > 0 and id2 > 0 and id3 > 0

    # list should be ordered by created_at DESC
    items = list_entries(db, user, limit=2)
    assert [i["text"] for i in items] == ["third", "second"], "Order and limit"

    # get specific
    e = get_entry(db, id2)
    assert e is not None
    assert e["id"] == id2
    assert e["text"] == "second"