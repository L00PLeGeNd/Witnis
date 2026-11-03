from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import explain_change
from witnis.mcp_server import build_server


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_explain_change_maps_symbols(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    target = repo / "auth.py"
    target.write_text(
        "class AuthService:\n    def login(self):\n        return True\n",
        encoding="utf-8",
    )
    _git(repo, "add", "auth.py")
    _git(repo, "commit", "-m", "add auth")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = explain_change(db, revision="HEAD")
    assert payload["status"] in {"success", "partial"}
    assert payload["result"]["commit"]["subject"] == "add auth"
    assert any(f["path"] == "auth.py" for f in payload["result"]["files"])
    names = {s["name"] for s in payload["result"]["symbols_in_touched_files"]}
    assert "AuthService" in names or "AuthService.login" in names
    assert payload["evidence"]
    assert payload["evidence"][0]["type"] == "commit"


def test_mcp_registers_explain_change() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "explain_change" in names
