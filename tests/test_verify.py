from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import (
    create_verification_plan,
    get_verification_report,
    run_verification,
)
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_create_verification_plan_is_read_only(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    plan = create_verification_plan(db, target="login")
    assert plan["status"] == "success"
    assert plan["result"]["state"] == "planned"
    assert plan["result"]["steps"]
    assert any("Plan only" in x for x in plan["limitations"])


def test_run_verification_blocked_without_auth(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    payload = run_verification(db, execute=True, target="login")
    assert payload["result"]["state"] == "blocked"


def test_run_verification_preview_without_execute(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = run_verification(db, execute=False, target="login")
    assert payload["result"]["state"] == "blocked"
    report = get_verification_report(db)
    assert report["result"]["state"] == "blocked"


def test_mcp_registers_verification_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert {
        "create_verification_plan",
        "run_verification",
        "get_verification_report",
    } <= names
