from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import trace_symbol

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_indexes_name_references(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        refs = store.find_relations(relation_type="references", target_equals="AuthService")
    finally:
        store.close()
    assert refs, "expected AuthService name references"


def test_trace_includes_references(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = trace_symbol(db, "AuthService")
    assert payload["result"]["references"]
