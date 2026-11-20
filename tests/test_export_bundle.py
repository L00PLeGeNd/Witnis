from __future__ import annotations

import json
import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import export_evidence_bundle
from witnis.core.verify import create_verification_plan


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_export_evidence_bundle_for_symbol(tmp_path: Path) -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
    db = tmp_path / "index.sqlite"
    index_repository(fixture, db, incremental=False)
    payload = export_evidence_bundle(db, target="login")
    assert payload["status"] == "success"
    bundle = payload["result"]["bundle"]
    assert bundle["target"] == "login"
    assert bundle["overview"]
    assert bundle["trace"]
    assert bundle["impact"]
    assert bundle["related_tests"]
    assert payload["evidence"]


def test_plan_with_revision_includes_change_impact(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return True\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return False\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "flip")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    plan = create_verification_plan(db, revision="HEAD")
    step_ids = {s.get("id") for s in plan["result"]["steps"]}
    assert "change_impact_review" in step_ids
    assert plan["result"].get("change_impact")
