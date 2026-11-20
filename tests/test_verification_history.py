from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import list_verification_runs, run_verification
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_list_verification_runs_after_execute(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    payload = list_verification_runs(db)
    assert payload["status"] == "success"
    assert payload["result"]["count"] >= 1
    assert payload["result"]["runs"][0]["state"] == "verified"


def test_mcp_registers_list_verification_runs() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "list_verification_runs" in names
