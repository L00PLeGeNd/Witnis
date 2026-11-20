"""Seams: Java uses_type edges + analyze_impact Indirect via subclass typed use.

Public contracts:
- index emits relation_type=uses_type from enclosing type → referenced type
- analyze_impact(base) places subclass typed-users in result.transitive
"""

from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import analyze_impact

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "fixtures" / "semantic_java_di"


def test_controller_uses_type_user(tmp_path: Path) -> None:
    db = tmp_path / "di.sqlite"
    index_repository(DI, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="uses_type", limit=100)
        assert any(
            "UserController" in str(e.get("source"))
            and str(e.get("target")) == "User"
            for e in edges
        ), edges
    finally:
        store.close()


def test_impact_person_indirect_includes_controller(tmp_path: Path) -> None:
    db = tmp_path / "di.sqlite"
    index_repository(DI, db, incremental=False)
    payload = analyze_impact(db, "Person")
    result = payload["result"]
    direct = result.get("direct") or []
    transitive = result.get("transitive") or []
    assert any(
        "User" in str(e.get("source")) and e.get("relation_type") == "inherits"
        for e in direct
    ), direct
    pack = transitive + direct
    assert any("UserController" in str(e.get("source") or e.get("name") or "") for e in pack), {
        "direct": direct,
        "transitive": transitive,
    }
