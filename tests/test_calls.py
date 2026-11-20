from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import trace_symbol

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_indexes_call_from_main_to_login(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        calls = store.find_relations(relation_type="calls")
    finally:
        store.close()
    assert any(
        c["source"].endswith(":main")
        and c["target"] in {"login", "AuthService", "auth.AuthService", "auth.AuthService.login"}
        for c in calls
    ), calls


def test_resolves_qualified_method_call(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        calls = store.find_relations(
            relation_type="calls", target_equals="auth.AuthService.login"
        )
    finally:
        store.close()
    assert any(c["source"].endswith(":main") for c in calls), calls


def test_resolves_self_attr_method_call(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        calls = store.find_relations(
            relation_type="calls", target_equals="auth.AuthService.login"
        )
    finally:
        store.close()
    assert any(
        c["source"].endswith(":AccessGate.allow") for c in calls
    ), calls


def test_resolves_chained_ctor_method_call(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        calls = store.find_relations(
            relation_type="calls", target_equals="AccessGate.allow"
        )
    finally:
        store.close()
    assert any(c["source"].endswith(":guarded_entry") for c in calls), calls


def test_trace_symbol_includes_called_by(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = trace_symbol(db, "login")
    assert payload["result"]["called_by"]
    assert any(
        edge["source"].endswith(":main") for edge in payload["result"]["called_by"]
    )
