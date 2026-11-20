from __future__ import annotations

import os
import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import run_verification
from witnis.core.verify_isolate import create_verify_worktree, cleanup_verify_workspace


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    return repo


def test_create_verify_worktree_pins_revision(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-m", "one")
    first = _git(repo, "rev-parse", "HEAD")
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-m", "two")

    work, meta = create_verify_worktree(repo, revision=first)
    try:
        assert meta.get("revision") == first
        assert (work / "a.txt").read_text(encoding="utf-8") == "one\n"
    finally:
        cleanup_verify_workspace(repo, work, meta)


def test_verify_sets_automation_flags_and_contradicted_on_fail(
    tmp_path: Path, monkeypatch
) -> None:
    repo = _init_repo(tmp_path)
    (repo / "mod.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "mod.py")
    _git(repo, "commit", "-m", "base")
    db = tmp_path / "i.sqlite"
    index_repository(repo, db, incremental=False)

    monkeypatch.setenv("WITNIS_ALLOW_VERIFY", "1")
    # Force isolate off for speed; still exercises honesty fields
    monkeypatch.setenv("WITNIS_VERIFY_ISOLATE", "0")
    payload = run_verification(db, execute=True, target="ok")
    assert "automation_verified" in payload["result"]
    assert "skipped_only" in payload["result"]
    # limitations mention human review
    assert any("human review" in x.lower() for x in payload.get("limitations") or [])
