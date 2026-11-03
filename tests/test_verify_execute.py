from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import run_verification

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_run_verification_execute_pytest_on_fixture(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    execution = payload["result"].get("execution") or []
    test_step = next(s for s in execution if s.get("step_id") == "run_tests")
    assert test_step.get("status") == "verified", test_step
    assert payload["result"]["state"] == "verified"
