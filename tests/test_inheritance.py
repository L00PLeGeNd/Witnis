from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import analyze_impact, check_index_health

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_indexes_inheritance_edges(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="inherits", limit=50)
    finally:
        store.close()
    assert any(
        e.get("source", "").endswith("SecureAuth") and e.get("target") == "AuthService"
        for e in edges
    ), edges


def test_impact_includes_subclass(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = analyze_impact(db, "AuthService")
    direct = payload["result"]["direct"]
    assert any(
        e.get("relation_type") == "inherits" and str(e.get("source", "")).endswith("SecureAuth")
        for e in direct
    ), direct


def test_index_health_ok(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = check_index_health(db)
    assert payload["status"] == "success"
    assert payload["result"]["issues"] == []
