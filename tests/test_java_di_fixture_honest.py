"""Honest expectations for Spring-style DI fixture.

Semantic P0 now claims implements + injects + typed field calls.
Still out of scope: AOP proxies, generic erasure, multi-impl @Primary selection.
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
def test_di_edges_present_for_p0(tmp_path: Path) -> None:
    db = tmp_path / "di.sqlite"
    stats = index_repository(DI, db, incremental=False)
    assert stats.files >= 4
    store = Store(db)
    try:
        inject = store.find_relations(relation_type="injects", limit=50)
        impl = store.find_relations(relation_type="implements", limit=50)
        assert inject, "expected @Autowired/ctor injects edges"
        assert impl, "expected implements edges"
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
