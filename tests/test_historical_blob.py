from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import explain_change


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_explain_change_reads_symbols_from_historical_blob(tmp_path: Path) -> None:
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

    # Mutate working tree away from HEAD so current-index mapping would miss AuthService
    target.write_text("class Unrelated:\n    pass\n", encoding="utf-8")
    index_repository(repo, db, incremental=False)

    payload = explain_change(db, revision="HEAD")
    names = {s["name"] for s in payload["result"]["symbols_in_touched_files"]}
    assert "AuthService" in names or "AuthService.login" in names
    assert any(e.get("type") == "historical_symbol" for e in payload["evidence"])
    assert not any(
        "not the historical blob" in x for x in (payload.get("limitations") or [])
    )
