from __future__ import annotations

from pathlib import Path

from witnis.core.verify_isolate import (
    cleanup_verify_workspace,
    create_verify_worktree,
    run_isolated_command,
    scrubbed_env,
    snapshot_tree,
)


def test_scrubbed_env_marks_network_deny() -> None:
    env = scrubbed_env(allow_network=False)
    assert env.get("WITNIS_VERIFY_NETWORK") == "deny"
    assert env.get("WITNIS_VERIFY_ISOLATED") == "1"


def test_worktree_or_copy_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("x=1\n", encoding="utf-8")
    work, meta = create_verify_worktree(repo)
    try:
        assert work.is_dir()
        assert meta["mode"] in {"worktree", "copy"}
        assert (work / "a.py").is_file()
    finally:
        cleanup_verify_workspace(repo, work, meta)


def test_fs_diff_detects_change(tmp_path: Path) -> None:
    root = tmp_path / "t"
    root.mkdir()
    f = root / "f.txt"
    f.write_text("a", encoding="utf-8")
    before = snapshot_tree(root)
    f.write_text("b", encoding="utf-8")
    after = snapshot_tree(root)
    diff = before.diff(after)
    assert "f.txt" in diff["changed"]


def test_isolated_command_runs_python(tmp_path: Path) -> None:
    import sys

    out = run_isolated_command(
        [sys.executable, "-c", "print(1)"],
        cwd=tmp_path,
        timeout_sec=30,
    )
    assert out.get("exit_code") == 0
    assert out.get("isolated") is True
