from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import check_import_graph
from witnis.core.verify import create_verification_plan, run_verification
import os

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_import_graph_ok_on_fixture(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = check_import_graph(db)
    assert payload["status"] == "success"
    assert payload["result"]["broken"] == []


def test_plan_includes_graph_check(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    plan = create_verification_plan(db, target="login")
    kinds = {s.get("kind") for s in plan["result"]["steps"]}
    assert "graph" in kinds


def test_execute_runs_graph_check(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    by_id = {s.get("step_id"): s for s in payload["result"]["execution"]}
    assert by_id["import_graph"]["status"] == "verified"
