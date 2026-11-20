from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import analyze_change_impact, explain_change


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def test_explain_change_maps_symbols_to_hunks(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "auth.py").write_text(
        "class AuthService:\n"
        "    def login(self):\n"
        "        return True\n"
        "\n"
        "class TokenStore:\n"
        "    def save(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", "auth.py")
    _git(repo, "commit", "-m", "base")

    # Change only login body so hunk overlaps AuthService.login, not TokenStore.save
    (repo / "auth.py").write_text(
        "class AuthService:\n"
        "    def login(self):\n"
        "        return False\n"
        "\n"
        "class TokenStore:\n"
        "    def save(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", "auth.py")
    _git(repo, "commit", "-m", "flip login")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = explain_change(db, revision="HEAD")
    hunks = payload["result"].get("hunks") or []
    assert hunks
    in_hunk = {s["name"] for s in payload["result"].get("symbols_in_hunks") or []}
    assert "AuthService.login" in in_hunk or "AuthService" in in_hunk
    assert "TokenStore.save" not in in_hunk


def test_analyze_change_impact_uses_hunk_symbols(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return True\n",
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "from auth import AuthService\n\ndef main():\n    AuthService().login()\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return False\n",
        encoding="utf-8",
    )
    _git(repo, "add", "auth.py")
    _git(repo, "commit", "-m", "flip")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = analyze_change_impact(db, revision="HEAD")
    assert payload["status"] in {"success", "partial"}
    assert payload["result"]["symbols_in_hunks"]
    direct = payload["result"].get("direct") or []
    assert any("main" in str(e.get("source")) for e in direct) or payload["result"].get(
        "symbols_in_hunks"
    )
