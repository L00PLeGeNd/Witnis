from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import (
    export_relation_graph,
    list_test_results,
    refresh_index,
)
from witnis.core.verify import run_verification
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_export_relation_graph_mermaid(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = export_relation_graph(db, "login", fmt="mermaid")
    assert payload["status"] in {"success", "partial"}
    assert "flowchart LR" in payload["result"]["graph"]
    assert payload["result"]["edge_count"] >= 1


def test_export_relation_graph_dot(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = export_relation_graph(db, "AuthService", fmt="dot")
    assert "digraph witnis" in payload["result"]["graph"]


def test_refresh_index_incremental(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = refresh_index(db)
    assert payload["status"] == "success"
    assert payload["result"]["skipped_unchanged"] >= 1


def test_verify_persists_test_results(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    payload = list_test_results(db)
    assert payload["result"]["count"] >= 1
    steps = {r.get("step_id") for r in payload["result"]["results"]}
    assert "run_tests" in steps or "syntax_check" in steps


def test_mcp_registers_graph_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert {
        "export_relation_graph",
        "refresh_index",
        "list_test_results",
    } <= names
