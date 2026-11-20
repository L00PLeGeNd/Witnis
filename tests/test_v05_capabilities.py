from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import (
    compare_worktree,
    list_capabilities,
    scan_secrets,
    trace_symbol,
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


def test_trace_includes_override_and_decorator(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = trace_symbol(db, "AuthService.login")
    assert payload["result"]["decorated_by"] or payload["result"]["overrides"] is not None
    # SecureAuth.login overrides AuthService.login — visible from either side
    over = trace_symbol(db, "SecureAuth.login")
    assert any(
        e.get("relation_type") == "overrides" or e.get("target") == "AuthService.login"
        for e in over["result"]["overrides"]
    ), over["result"]["overrides"]


def test_compare_worktree_detects_new_symbol(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "mod.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "alpha")
    (repo / "mod.py").write_text(
        "def alpha():\n    return 1\n\ndef gamma():\n    return 3\n",
        encoding="utf-8",
    )
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = compare_worktree(db)
    added = {s["name"] for s in payload["result"]["symbols_added"]}
    assert "gamma" in added


def test_scan_secrets_finds_assignment(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / "cfg.py").write_text(
        "password = 'sk-test-should-redact'\n", encoding="utf-8"
    )
    db = tmp_path / "index.sqlite"
    stats = index_repository(repo, db, incremental=False)
    assert stats.files >= 1
    assert (repo / "cfg.py").read_text(encoding="utf-8").startswith("password")
    payload = scan_secrets(db)
    assert payload["result"]["scanned_files"] >= 1, payload
    assert payload["result"]["finding_count"] >= 1, payload
    assert "REDACTED" in payload["result"]["findings"][0]["preview"]


def test_list_capabilities() -> None:
    payload = list_capabilities()
    assert payload["status"] == "success"
    assert "index" in payload["result"]["cli_commands"]
    assert payload["result"]["mcp_tools"] == ["index", "look", "impact", "verify"]
    assert "run_verification" in payload["result"]["mcp_experimental"]
    assert payload["result"]["version"]


def test_mcp_registers_v05_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert {
        "compare_worktree",
        "scan_secrets",
        "list_capabilities",
    } <= names
