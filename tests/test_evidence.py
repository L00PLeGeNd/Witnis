from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import get_evidence
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_get_evidence_for_login(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = get_evidence(db, "login")
    assert payload["evidence"]
    assert payload["result"]["symbols"] or payload["result"]["relations"]


def test_mcp_registers_get_evidence() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "get_evidence" in names
