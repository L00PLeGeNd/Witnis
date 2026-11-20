from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store


def test_incremental_skips_unchanged(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    target = repo / "mod.py"
    target.write_text("def alpha():\n    return 1\n", encoding="utf-8")
    db = tmp_path / "index.sqlite"

    first = index_repository(repo, db, incremental=True)
    assert first.updated_files == 1
    assert first.skipped_unchanged == 0

    second = index_repository(repo, db, incremental=True)
    assert second.updated_files == 0
    assert second.skipped_unchanged == 1
    assert second.symbols == first.symbols

    target.write_text(
        "def alpha():\n    return 1\n\ndef beta():\n    return 2\n",
        encoding="utf-8",
    )
    third = index_repository(repo, db, incremental=True)
    assert third.updated_files == 1
    assert third.skipped_unchanged == 0

    store = Store(db)
    try:
        hits = store.search("beta")
    finally:
        store.close()
    assert any(h["name"] == "beta" for h in hits)


def test_incremental_removes_deleted_file(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    keep = repo / "keep.py"
    drop = repo / "drop.py"
    keep.write_text("def keep():\n    return 1\n", encoding="utf-8")
    drop.write_text("def drop():\n    return 1\n", encoding="utf-8")
    db = tmp_path / "index.sqlite"

    index_repository(repo, db, incremental=True)
    drop.unlink()
    stats = index_repository(repo, db, incremental=True)
    assert stats.removed_files == 1

    store = Store(db)
    try:
        assert store.search("drop") == []
        assert store.search("keep")
    finally:
        store.close()
