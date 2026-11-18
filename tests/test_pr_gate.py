from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.gitinfo import (
    git_merge_base,
    git_name_status_range,
    git_name_status_triple_dot,
)
from witnis.core.index import index_repository
from witnis.core.pr_gate import (
    analyze_pr_impact,
    evaluate_pr_gate_exit,
    render_pr_gate_markdown,
    run_pr_gate,
)


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


def test_triple_dot_differs_from_two_dot_when_main_advances(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-m", "root")
    _git(repo, "branch", "main")

    _git(repo, "checkout", "-b", "feature")
    (repo / "feat.py").write_text("def feat():\n    return 2\n", encoding="utf-8")
    _git(repo, "add", "feat.py")
    _git(repo, "commit", "-m", "feature work")

    _git(repo, "checkout", "main")
    (repo / "main_only.py").write_text("def main_only():\n    return 3\n", encoding="utf-8")
    _git(repo, "add", "main_only.py")
    _git(repo, "commit", "-m", "main advances")

    feature = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "feature"], text=True
    ).strip()
    main = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "main"], text=True
    ).strip()

    two = {c["path"] for c in git_name_status_range(repo, main, feature)}
    three = {c["path"] for c in git_name_status_triple_dot(repo, main, feature)}
    assert "feat.py" in three
    assert "main_only.py" not in three
    # two-dot tip-to-tip includes divergence both ways
    assert "main_only.py" in two or "feat.py" in two
    mb = git_merge_base(repo, main, feature)
    assert mb


def test_analyze_pr_impact_uses_three_dot_files(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "svc.py").write_text(
        "class Svc:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "from svc import Svc\n\ndef main():\n    return Svc().run()\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "main")
    _git(repo, "checkout", "-b", "pr")
    (repo / "svc.py").write_text(
        "class Svc:\n    def run(self):\n        return 0\n",
        encoding="utf-8",
    )
    _git(repo, "add", "svc.py")
    _git(repo, "commit", "-m", "flip")

    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = analyze_pr_impact(db, base_ref="main", head_ref="pr")
    assert payload["result"]["analysis_scope"] == "pr_range"
    assert payload["result"]["merge_base"]["hash"]
    paths = {f["path"] for f in payload["result"]["files"]}
    assert "svc.py" in paths
    assert payload["result"]["symbols_in_hunks"] or payload["result"]["direct"] is not None


def test_pr_gate_markdown_contains_status_sections(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "x.py").write_text("def x():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "x.py")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "main")
    _git(repo, "checkout", "-b", "pr")
    (repo / "x.py").write_text("def x():\n    return 2\n", encoding="utf-8")
    _git(repo, "add", "x.py")
    _git(repo, "commit", "-m", "change")

    db = tmp_path / "i.sqlite"
    payload = run_pr_gate(
        db,
        base_ref="main",
        head_ref="pr",
        root=repo,
        reindex=True,
        with_plan=True,
        execute_verify=False,
    )
    md = payload["markdown"]
    assert "Witnis PR evidence gate" in md
    assert "Evidence status counts" in md
    assert "merge_base" in md
    assert "blocked" in md.lower() or "Verify" in md
    assert "not human review" in md.lower() or "Harnis" in md
    assert evaluate_pr_gate_exit(payload, strict=False) == 0
