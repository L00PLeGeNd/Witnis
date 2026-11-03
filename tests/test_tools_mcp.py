from __future__ import annotations

import json
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import repo_overview, repo_search, trace_symbol
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_repo_search_envelope(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db)
    payload = repo_search(db, "login")
    assert payload["status"] == "success"
    assert payload["evidence"]
    assert payload["evidence"][0]["status"] == "observed"
    assert any("login" in m["name"] for m in payload["result"]["matches"])


def test_repo_overview_envelope(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db)
    payload = repo_overview(db)
    assert payload["status"] == "success"
    assert payload["result"]["symbols"] >= 3


def test_trace_symbol_auth_service(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db)
    payload = trace_symbol(db, "AuthService")
    assert payload["result"]["definitions"]
    assert payload["evidence"]


def test_mcp_tool_names_registered() -> None:
    server = build_server()
    tools = server._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert {
        "repo_overview",
        "repo_search",
        "trace_symbol",
        "explain_change",
        "analyze_impact",
        "find_related_tests",
    } <= names

