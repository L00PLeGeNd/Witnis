from __future__ import annotations

from pathlib import Path

import pytest

from witnis.core.verify_isolate import (
    cleanup_verify_workspace,
    create_verify_worktree,
    detect_container_runtime,
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


def test_container_profile_fails_closed_without_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "witnis.core.verify_isolate.detect_container_runtime", lambda: None
    )
    out = run_isolated_command(
        ["python3", "-c", "print(1)"],
        cwd=tmp_path,
        profile="container",
        timeout_sec=10,
    )
    assert out.get("exit_code") == 127
    assert out.get("profile") == "container"
    assert out.get("container_runtime") is None


def test_container_profile_runs_python_with_network_none(tmp_path: Path) -> None:
    if detect_container_runtime() is None:
        pytest.skip("docker/podman daemon not running")
    (tmp_path / "probe.py").write_text("print('isolated-ok')\n", encoding="utf-8")
    out = run_isolated_command(
        ["python3", "probe.py"],
        cwd=tmp_path,
        profile="container",
        timeout_sec=120,
    )
    assert out.get("exit_code") == 0, out
    assert out.get("profile") == "container"
    assert out.get("container_runtime") in {"docker", "podman"}
    assert out.get("network") == "none"
    assert "isolated-ok" in (out.get("stdout") or "")
