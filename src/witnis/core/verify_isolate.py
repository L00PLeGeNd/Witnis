"""Isolated verification execution helpers.

Authorize gate (WITNIS_ALLOW_VERIFY) remains required. This module adds
execution boundaries: disposable worktree, timeouts, env scrub, FS snapshot.
Not a full container sandbox — see SECURITY.md.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FsSnapshot:
    """Relative path → sha256 for regular files under root (capped)."""

    files: dict[str, str] = field(default_factory=dict)

    def diff(self, other: "FsSnapshot") -> dict[str, list[str]]:
        added = sorted(set(other.files) - set(self.files))
        removed = sorted(set(self.files) - set(other.files))
        changed = sorted(
            p for p in set(self.files) & set(other.files) if self.files[p] != other.files[p]
        )
        return {"added": added, "removed": removed, "changed": changed}


def snapshot_tree(root: Path, *, limit: int = 5000) -> FsSnapshot:
    out: dict[str, str] = {}
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in {".git", ".witnis", "__pycache__", "node_modules", "target"} for part in path.parts):
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
        out[rel] = digest
        count += 1
        if count >= limit:
            break
    return FsSnapshot(files=out)


def create_verify_worktree(
    repo_root: Path, *, revision: str | None = None
) -> tuple[Path, dict[str, Any]]:
    """Create a disposable git worktree (or file copy fallback) for verify.

    When ``revision`` is set, the worktree is detached at that commit (not ambient HEAD).
    """
    meta: dict[str, Any] = {"mode": "copy"}
    pin = (revision or "HEAD").strip() or "HEAD"
    tmp = Path(tempfile.mkdtemp(prefix="witnis-verify-"))
    git_dir = repo_root / ".git"
    if git_dir.exists():
        branch = f"witnis-verify-{os.getpid()}"
        try:
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(tmp), pin],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            meta = {
                "mode": "worktree",
                "path": str(tmp),
                "branch": branch,
                "revision": pin,
            }
            return tmp, meta
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            shutil.rmtree(tmp, ignore_errors=True)
            tmp = Path(tempfile.mkdtemp(prefix="witnis-verify-"))
    # Fallback: copy tree without .git bulk if possible
    def _ignore(dirpath: str, names: list[str]) -> set[str]:
        skip = {".git", ".witnis", "__pycache__", "node_modules", "target", ".venv", "venv"}
        return {n for n in names if n in skip}

    shutil.copytree(repo_root, tmp, dirs_exist_ok=True, ignore=_ignore)
    meta = {"mode": "copy", "path": str(tmp)}
    return tmp, meta


def cleanup_verify_workspace(repo_root: Path, work: Path, meta: dict[str, Any]) -> None:
    if meta.get("mode") == "worktree":
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(work)],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            shutil.rmtree(work, ignore_errors=True)
    else:
        shutil.rmtree(work, ignore_errors=True)


def scrubbed_env(*, allow_network: bool = False) -> dict[str, str]:
    """Minimal env for verify children. Network deny is best-effort (no proxy unset alone)."""
    keep = {
        "PATH",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TMP",
        "TEMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "WITNIS_ALLOW_VERIFY",
    }
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["WITNIS_VERIFY_ISOLATED"] = "1"
    if not allow_network:
        # Hint for tools that honor these; not a kernel firewall.
        env["WITNIS_VERIFY_NETWORK"] = "deny"
        env.pop("HTTP_PROXY", None)
        env.pop("HTTPS_PROXY", None)
        env.pop("ALL_PROXY", None)
        env.pop("http_proxy", None)
        env.pop("https_proxy", None)
    return env


def detect_container_runtime() -> str | None:
    """Return 'docker' or 'podman' if available on PATH and responsive, else None."""
    preferred = os.environ.get("WITNIS_CONTAINER_RUNTIME", "").strip().lower()
    candidates = [preferred] if preferred in {"docker", "podman"} else ["docker", "podman"]
    for bin_name in candidates:
        if not shutil.which(bin_name):
            continue
        try:
            proc = subprocess.run(
                [bin_name, "version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0:
                return bin_name
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def build_container_command(
    cmd: list[str],
    *,
    cwd: Path,
    runtime: str = "docker",
    image: str | None = None,
    allow_network: bool = False,
) -> list[str]:
    """Wrap an allowlisted verify command into a rootless/network-none container invocation."""
    img = image or os.environ.get("WITNIS_VERIFY_IMAGE", "python:3.12-slim")
    # Convert python absolute executable path to 'python3' inside container
    inner_cmd = list(cmd)
    if inner_cmd and Path(inner_cmd[0]).name.lower().startswith("python"):
        inner_cmd[0] = "python3"
    net_flag = "bridge" if allow_network else "none"
    # Source is mounted :ro; bytecode and pytest cache must land on tmpfs.
    return [
        runtime,
        "run",
        "--rm",
        "--network",
        net_flag,
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-e",
        "PYTHONPYCACHEPREFIX=/tmp/pycache",
        "-e",
        "PYTEST_ADDOPTS=-p no:cacheprovider --basetemp=/tmp/pytest-tmp",
        "-e",
        "PYTHONPATH=/work/src:/work",
        "-e",
        "HOME=/tmp",
        "-v",
        f"{cwd.resolve()}:/work:ro",
        "-w",
        "/work",
        img,
        *inner_cmd,
    ]


def run_isolated_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout_sec: int = 120,
    allow_network: bool = False,
    profile: str = "worktree",
) -> dict[str, Any]:
    before = snapshot_tree(cwd)
    exec_cmd = cmd
    isolation_profile = profile
    container_runtime: str | None = None

    if profile == "container":
        container_runtime = detect_container_runtime()
        if container_runtime is None:
            return {
                "exit_code": 127,
                "status": "failed",
                "stdout": "",
                "stderr": "Container profile requested but neither docker nor podman is available",
                "fs_diff": before.diff(before),
                "isolated": True,
                "profile": "container",
                "container_runtime": None,
                "network": "none",
            }
        exec_cmd = build_container_command(
            cmd,
            cwd=cwd,
            runtime=container_runtime,
            allow_network=allow_network,
        )

    try:
        proc = subprocess.run(
            exec_cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=scrubbed_env(allow_network=allow_network),
        )
        after = snapshot_tree(cwd)
        return {
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
            "fs_diff": before.diff(after),
            "isolated": True,
            "profile": isolation_profile,
            "container_runtime": container_runtime,
            "network": "allow" if allow_network else ("none" if profile == "container" else "deny-hint"),
        }
    except subprocess.TimeoutExpired:
        after = snapshot_tree(cwd)
        return {
            "exit_code": None,
            "status": "timeout",
            "fs_diff": before.diff(after),
            "isolated": True,
            "profile": isolation_profile,
            "container_runtime": container_runtime,
        }
