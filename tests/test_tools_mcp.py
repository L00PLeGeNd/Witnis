from __future__ import annotations

import json
from pathlib import Path

import pytest

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


@pytest.mark.mcp_public
def test_mcp_public_surface_is_four_tools() -> None:
    server = build_server()
    names = {t.name for t in server._tool_manager.list_tools()}
    assert names == {"index", "look", "impact", "verify"}


def test_mcp_experimental_restores_full_catalog(monkeypatch) -> None:
    monkeypatch.setenv("WITNIS_MCP_EXPERIMENTAL", "1")
    server = build_server()
    names = {t.name for t in server._tool_manager.list_tools()}
    assert {"index", "look", "impact", "verify"} <= names
    assert "analyze_impact" in names
    assert "repo_search" in names

