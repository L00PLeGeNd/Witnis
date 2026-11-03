from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_incremental_matches_full_rebuild_counts(tmp_path: Path) -> None:
    full_db = tmp_path / "full.sqlite"
    inc_db = tmp_path / "inc.sqlite"
    full = index_repository(FIXTURE, full_db, incremental=False)
    # seed then no-op incremental
    index_repository(FIXTURE, inc_db, incremental=False)
    again = index_repository(FIXTURE, inc_db, incremental=True)
    assert again.skipped_unchanged >= 1
    assert again.updated_files == 0
    assert again.files == full.files
    assert again.symbols == full.symbols

    # mutate one file and ensure counts stay coherent vs full rebuild
    target = FIXTURE / "auth.py"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original + "\nEXTRA = 1\n", encoding="utf-8")
        index_repository(FIXTURE, inc_db, incremental=True)
        rebuilt = index_repository(FIXTURE, tmp_path / "re.sqlite", incremental=False)
        store = Store(inc_db)
        try:
            ov = store.overview()
            assert ov["files"] == rebuilt.files
            assert ov["symbols"] == rebuilt.symbols
        finally:
            store.close()
    finally:
        target.write_text(original, encoding="utf-8")
