from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import create_verification_plan, run_verification

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_plan_includes_static_compile_step(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    plan = create_verification_plan(db, target="login")
    kinds = {s.get("kind") for s in plan["result"]["steps"]}
    assert "static" in kinds
    static = next(s for s in plan["result"]["steps"] if s.get("kind") == "static")
    cmd = static.get("command") or []
    assert "-m" in cmd and "compileall" in cmd


def test_execute_runs_static_and_pytest(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    execution = payload["result"].get("execution") or []
    by_id = {s.get("step_id"): s for s in execution}
    assert by_id["static_compile"]["status"] == "verified"
    assert by_id["run_tests"]["status"] == "verified"
    assert payload["result"]["state"] == "verified"
