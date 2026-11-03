from __future__ import annotations

import os
import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import check_python_syntax, compare_revisions
from witnis.core.verify import create_verification_plan, run_verification

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_syntax_check_ok_on_fixture(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = check_python_syntax(db, paths=["auth.py", "app.py"])
    assert payload["status"] == "success"
    assert payload["result"]["errors"] == []


def test_plan_and_execute_include_syntax(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    plan = create_verification_plan(db, target="login")
    assert any(s.get("kind") == "syntax" for s in plan["result"]["steps"])
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    by_id = {s.get("step_id"): s for s in payload["result"]["execution"]}
    assert by_id["syntax_check"]["status"] == "verified"


def test_compare_revisions_js_symbol_delta(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "util.ts").write_text(
        "export function alpha(): number { return 1 }\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "alpha")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (repo / "util.ts").write_text(
        "export function alpha(): number { return 1 }\n"
        "export function beta(): number { return 2 }\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "beta")
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = compare_revisions(db, base=base, head="HEAD")
    added = {s["name"] for s in payload["result"]["symbols_added"]}
    assert "beta" in added


def test_compare_revisions_symbol_delta(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "mod.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "alpha")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (repo / "mod.py").write_text(
        "def alpha():\n    return 1\n\ndef beta():\n    return 2\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "beta")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = compare_revisions(db, base=base, head="HEAD")
    assert payload["status"] in {"success", "partial"}
    added = {s["name"] for s in payload["result"]["symbols_added"]}
    assert "beta" in added
