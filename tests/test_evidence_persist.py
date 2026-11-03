from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import get_evidence
from witnis.core.verify import run_verification

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_verify_persists_verified_evidence(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    assert payload["result"]["state"] == "verified"

    filtered = get_evidence(db, "login", status="verified")
    assert filtered["result"]["stored_count"] >= 1
    assert any(e.get("status") == "verified" for e in filtered["evidence"])
