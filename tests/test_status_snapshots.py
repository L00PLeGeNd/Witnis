from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import (
    explain_change,
    list_commits,
    list_index_snapshots,
    render_evidence_report,
    repo_status,
)
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_index_records_snapshots(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    index_repository(FIXTURE, db, incremental=True)
    payload = list_index_snapshots(db)
    assert payload["result"]["count"] >= 2
    modes = {s.get("mode") for s in payload["result"]["snapshots"]}
    assert "full" in modes
    assert "incremental" in modes


def test_list_commits_after_explain_change(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "add f")
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    explain_change(db, revision="HEAD")
    payload = list_commits(db)
    assert payload["result"]["count"] >= 1
    assert payload["result"]["commits"][0]["subject"] == "add f"


def test_repo_status_aggregate(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = repo_status(db)
    assert payload["status"] == "success"
    assert payload["result"]["overview"]["symbols"] >= 1
    assert "issues" in payload["result"]["health"]
    assert payload["result"]["snapshots"]


def test_report_includes_html(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = render_evidence_report(db, target="login")
    assert "<!doctype html>" in payload["result"]["html"].lower()
    assert "Witnis evidence report" in payload["result"]["html"]


def test_mcp_registers_status_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert {
        "repo_status",
        "list_commits",
        "list_index_snapshots",
    } <= names
