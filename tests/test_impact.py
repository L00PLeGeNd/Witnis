from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact, find_related_tests
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_analyze_impact_login_has_direct_caller(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = analyze_impact(db, "login")
    assert payload["status"] in {"success", "partial"}
    direct = payload["result"]["direct"]
    assert any(
        e.get("target") == "login" and str(e.get("source", "")).endswith(":main")
        for e in direct
    ), direct


def test_analyze_impact_auth_service_sees_import(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = analyze_impact(db, "AuthService")
    assert payload["result"]["direct"]


def test_find_related_tests_finds_fixture_test(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = find_related_tests(db, "login")
    assert payload["status"] == "success"
    assert any(
        "test_auth.py" in str(t.get("file_path")) for t in payload["result"]["tests"]
    ), payload["result"]["tests"]


def test_mcp_registers_impact_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert {"analyze_impact", "find_related_tests", "explain_change"} <= names
