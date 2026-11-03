"""Honest expectations for Spring-style DI fixture.

Documents what shallow Java can and cannot claim today.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from witnis.core.index import index_repository
from witnis.core.store import Store

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "fixtures" / "semantic_java_di"


@pytest.mark.skipif(not DI.is_dir(), reason="semantic_java_di missing")
def test_di_fixture_files_present() -> None:
    needed = [
        "com/example/user/UserService.java",
        "com/example/user/UserRepository.java",
        "com/example/user/JdbcUserRepository.java",
        "com/example/user/UserController.java",
    ]
    for rel in needed:
        assert (DI / rel).is_file(), rel


@pytest.mark.skipif(not DI.is_dir(), reason="semantic_java_di missing")
def test_shallow_java_indexes_without_claiming_injection(tmp_path: Path) -> None:
    db = tmp_path / "di.sqlite"
    stats = index_repository(DI, db, incremental=False)
    assert stats.files >= 4

    store = Store(db)
    try:
        repo_id = store.conn.execute("SELECT id FROM repositories LIMIT 1").fetchone()[0]
        rels = store.list_relations(repo_id, limit=500)
        inject = [
            r
            for r in rels
            if str(r.get("relation_type") or "").lower()
            in {"injects", "inject", "autowired", "di"}
        ]
        assert inject == [], (
            "Unexpected DI edges claimed by shallow indexer — "
            "either implement intentionally or stop emitting them: "
            f"{inject}"
        )
    finally:
        store.close()


@pytest.mark.skipif(not DI.is_dir(), reason="semantic_java_di missing")
def test_ground_truth_label_file_loads() -> None:
    path = ROOT / "benchmarks" / "ground-truth" / "labels" / "semantic_java_di.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["id"] == "semantic_java_di"
    kinds = {t["kind"] for t in data["tasks"]}
    assert "call_edge" in kinds
    assert "symbol_locate" in kinds
