from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(root: Path, *args: str, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def git_toplevel(root: Path) -> Path | None:
    try:
        proc = _run_git(root, "rev-parse", "--show-toplevel", timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return Path(value).resolve() if value else None


def git_head(root: Path) -> str | None:
    """Return HEAD commit hash if root is inside a git work tree."""
    try:
        proc = _run_git(root, "rev-parse", "HEAD", timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def git_commit_summary(root: Path, revision: str = "HEAD") -> dict | None:
    """Return basic commit metadata for revision."""
    try:
        proc = _run_git(
            root,
            "show",
            "-s",
            "--format=%H%n%an%n%ae%n%cI%n%s",
            revision,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    lines = proc.stdout.splitlines()
    if len(lines) < 5:
        return None
    return {
        "hash": lines[0],
        "author_name": lines[1],
        "author_email": lines[2],
        "committed_at": lines[3],
        "subject": lines[4],
    }


def git_name_status(root: Path, revision: str = "HEAD") -> list[dict]:
    """List files changed in revision (vs its parent)."""
    try:
        proc = _run_git(
            root,
            "show",
            "--name-status",
            "--format=",
            revision,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    changes: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.append(
                {
                    "status": "R",
                    "path": parts[2],
                    "from_path": parts[1],
                }
            )
        else:
            changes.append({"status": status[0], "path": parts[1]})
    return changes


def _parse_name_status(stdout: str) -> list[dict]:
    changes: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.append({"status": "R", "path": parts[2], "from_path": parts[1]})
        else:
            changes.append({"status": status[0], "path": parts[1]})
    return changes


def git_name_status_range(root: Path, base: str, head: str) -> list[dict]:
    """List files changed between two revisions (base..head)."""
    try:
        proc = _run_git(
            root,
            "diff",
            "--name-status",
            f"{base}..{head}",
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    return _parse_name_status(proc.stdout)


def git_worktree_name_status(root: Path) -> list[dict]:
    """List unstaged+staged worktree changes vs HEAD."""
    try:
        proc = _run_git(root, "diff", "--name-status", "HEAD", timeout=20)
        cached = _run_git(root, "diff", "--name-status", "--cached", "HEAD", timeout=20)
        untracked = _run_git(
            root, "ls-files", "--others", "--exclude-standard", timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    changes = _parse_name_status(proc.stdout if proc.returncode == 0 else "")
    if cached.returncode == 0:
        changes.extend(_parse_name_status(cached.stdout))
    # de-dupe by path keeping first status
    seen: set[str] = set()
    out: list[dict] = []
    for row in changes:
        path = str(row.get("path") or "")
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(row)
    if untracked.returncode == 0:
        for line in untracked.stdout.splitlines():
            path = line.strip()
            if path and path not in seen:
                seen.add(path)
                out.append({"status": "?", "path": path})
    return out


def git_diff_hunks(root: Path, revision: str = "HEAD") -> list[dict]:
    """Parse unified diff hunks for a revision (new-file line ranges)."""
    try:
        proc = _run_git(
            root,
            "show",
            "--unified=0",
            "--format=",
            revision,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []

    hunks: list[dict] = []
    current_path: str | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_path = None if path == "/dev/null" else path
            continue
        if not line.startswith("@@") or current_path is None:
            continue
        # @@ -old_start,old_count +new_start,new_count @@
        try:
            plus = line.split(" ")[2]  # +start,count
            if not plus.startswith("+"):
                continue
            body = plus[1:]
            if "," in body:
                start_s, count_s = body.split(",", 1)
                start = int(start_s)
                count = int(count_s)
            else:
                start = int(body)
                count = 1
        except (IndexError, ValueError):
            continue
        if count <= 0:
            # pure deletion: keep a zero-width anchor at the prior line
            hunks.append(
                {
                    "path": current_path,
                    "start_line": max(1, start),
                    "end_line": max(1, start),
                    "new_count": 0,
                }
            )
            continue
        hunks.append(
            {
                "path": current_path,
                "start_line": start,
                "end_line": start + count - 1,
                "new_count": count,
            }
        )
    return hunks


def git_show_blob(root: Path, revision: str, rel_path: str) -> str | None:
    """Return file contents at revision:path, or None if unavailable."""
    spec = f"{revision}:{rel_path.replace(chr(92), '/')}"
    try:
        proc = _run_git(root, "show", spec, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_blame_range(
    root: Path, rel_path: str, start_line: int, end_line: int
) -> list[dict]:
    """Return blame rows for an inclusive line range."""
    if start_line < 1 or end_line < start_line:
        return []
    try:
        proc = _run_git(
            root,
            "blame",
            "-L",
            f"{start_line},{end_line}",
            "--line-porcelain",
            "--",
            rel_path,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []

    rows: list[dict] = []
    current: dict | None = None
    for line in proc.stdout.splitlines():
        if not line:
            continue
        parts = line.split()
        # porcelain commit header starts with 40-char hex sha
        if (
            len(parts) >= 3
            and len(parts[0]) >= 40
            and all(c in "0123456789abcdef" for c in parts[0][:40])
        ):
            if current:
                rows.append(current)
            try:
                line_no = int(parts[2])
            except ValueError:
                line_no = None
            current = {
                "commit": parts[0],
                "line": line_no,
                "author": None,
                "summary": None,
            }
            continue
        if current is None:
            continue
        if line.startswith("author "):
            current["author"] = line[len("author ") :]
        elif line.startswith("summary "):
            current["summary"] = line[len("summary ") :]
        elif line.startswith("\t"):
            current["text"] = line[1:]
    if current:
        rows.append(current)
    return rows
