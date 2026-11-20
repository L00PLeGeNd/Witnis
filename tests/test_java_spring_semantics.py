"""Seam: Java relation extraction for Spring-style DI fixtures.

Public contract: index_repository + Store.list_relations / find_relations
must emit implements + injects + typed calls — not name-only call noise alone.
"""

from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "fixtures" / "semantic_java_di"


def _index(tmp_path: Path) -> Store:
    db = tmp_path / "di.sqlite"
    index_repository(DI, db, incremental=False)
    return Store(db)


def test_implements_jdbc_user_repository(tmp_path: Path) -> None:
    store = _index(tmp_path)
    try:
        edges = store.find_relations(relation_type="implements", limit=50)
        assert any(
            "JdbcUserRepository" in str(e.get("source"))
            and "UserRepository" in str(e.get("target"))
            for e in edges
        ), edges
    finally:
        store.close()


def test_autowired_field_injects_user_repository(tmp_path: Path) -> None:
    store = _index(tmp_path)
    try:
        edges = store.find_relations(relation_type="injects", limit=50)
        assert any(
            "UserService" in str(e.get("source"))
            and "UserRepository" in str(e.get("target"))
            for e in edges
        ), edges
    finally:
        store.close()


def test_ctor_injects_user_service_into_controller(tmp_path: Path) -> None:
    store = _index(tmp_path)
    try:
        edges = store.find_relations(relation_type="injects", limit=50)
        assert any(
            "UserController" in str(e.get("source"))
            and "UserService" in str(e.get("target"))
            for e in edges
        ), edges
    finally:
        store.close()


def test_typed_call_controller_to_find_user(tmp_path: Path) -> None:
    store = _index(tmp_path)
    try:
        edges = store.find_relations(relation_type="calls", limit=200)
        assert any(
            "UserController" in str(e.get("source"))
            and "findUser" in str(e.get("target"))
            for e in edges
        ), edges
        assert any(
            "UserService" in str(e.get("target")) or "findUser" in str(e.get("target"))
            for e in edges
            if "UserController" in str(e.get("source"))
        ), edges
    finally:
        store.close()
