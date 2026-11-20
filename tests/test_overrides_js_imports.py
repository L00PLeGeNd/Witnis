from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import analyze_impact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PY = ROOT / "fixtures" / "mini_py"
FIXTURE_JS = ROOT / "fixtures" / "mini_js"


def test_indexes_method_overrides(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="overrides", limit=50)
    finally:
        store.close()
    assert any(
        str(e.get("source", "")).endswith("SecureAuth.login")
        and e.get("target") == "AuthService.login"
        for e in edges
    ), edges


def test_impact_sees_override(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    payload = analyze_impact(db, "AuthService.login")
    assert any(
        e.get("relation_type") == "overrides"
        and str(e.get("source", "")).endswith("SecureAuth.login")
        for e in payload["result"]["direct"]
    ), payload["result"]["direct"]


def test_indexes_js_imports(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JS, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="imports", limit=50)
    finally:
        store.close()
    assert any(
        e.get("source") == "app.ts" and "./auth" in str(e.get("target"))
        for e in edges
    ), edges
