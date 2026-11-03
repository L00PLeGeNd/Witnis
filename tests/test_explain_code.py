from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import explain_code
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_explain_code_includes_snippet(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = explain_code(db, "AuthService.login")
    assert payload["status"] == "success"
    assert payload["result"]["snippet"]
    assert payload["result"]["symbol"]["name"] == "AuthService.login"


def test_mcp_registers_explain_code() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "explain_code" in names
