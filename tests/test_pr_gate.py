from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from witnis.core.gitinfo import (
    git_merge_base,
    git_name_status_range,
    git_name_status_triple_dot,
)
from witnis.core.index import index_repository
from witnis.core.parse_java import parse_java_source
from witnis.core.pr_gate import (
    analyze_pr_impact,
    evaluate_pr_gate_exit,
    render_pr_gate_markdown,
    run_pr_gate,
)

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "fixtures" / "semantic_java_di"
PETCLINIC = (
    ROOT
    / "benchmarks"
    / "ground-truth"
    / "corpora"
    / "checkouts"
    / "spring-petclinic"
)
PETCLINIC_PIN = "500158f732419217507c7656904b8e6aa1bcc0d6"


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
    assert "cannot claim tests passed" in md.lower() or "blocked" in md.lower()
    assert "executed: **0**" in md or "Commands executed: **0**" in md or "0 command" in md.lower()
    assert "automation_verified" in md.lower()
    low = md.lower()
    assert "tests passed" not in low.split("cannot claim")[0] or "cannot claim tests passed" in low
    # Headline must not read as a successful verify.
    assert not md.lstrip().startswith("# Verified")
    assert evaluate_pr_gate_exit(payload, strict=False) == 0


def test_pr_gate_markdown_lists_transitive_when_blast_radius_is_full() -> None:
    """Person→Owner controllers must not vanish behind a 6-line blast hop of Direct calls."""
    direct = [
        {
            "relation_type": "calls",
            "source": f"Noise{i}.java:Noise{i}",
            "target": "Person",
        }
        for i in range(10)
    ]
    md = render_pr_gate_markdown(
        {
            "impact": {
                "status": "success",
                "repository": {},
                "result": {
                    "direct": direct,
                    "transitive": [
                        {
                            "relation_type": "uses_type",
                            "source": "OwnerController.java:OwnerController",
                            "target": "Owner",
                        },
                        {
                            "relation_type": "uses_type",
                            "source": "PetController.java:PetController",
                            "target": "Owner",
                        },
                        {
                            "relation_type": "uses_type",
                            "source": "VisitController.java:VisitController",
                            "target": "Owner",
                        },
                    ],
                },
                "evidence": [],
            }
        }
    )
    for name in ("OwnerController", "PetController", "VisitController"):
        assert name in md, name
    assert "**transitive edges:** 3" in md


def test_parse_java_class_span_covers_method_body() -> None:
    src = (DI / "com" / "example" / "user" / "Person.java").read_text(encoding="utf-8")
    syms = parse_java_source(src, rel_path="Person.java")
    person = next(s for s in syms if s.name == "Person" and s.kind == "class")
    getter = next(s for s in syms if s.name == "getName")
    assert person.end_line >= getter.start_line


def test_java_hunk_pr_gate_names_typed_controller(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    shutil.copytree(DI, repo)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "main")
    _git(repo, "checkout", "-b", "pr")
    person = repo / "com" / "example" / "user" / "Person.java"
    person.write_text(
        person.read_text(encoding="utf-8").replace(
            "return name;",
            'return name == null ? "" : name;',
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "com/example/user/Person.java")
    _git(repo, "commit", "-m", "touch Person getter")

    db = tmp_path / "index.sqlite"
    payload = run_pr_gate(
        db,
        base_ref="main",
        head_ref="pr",
        root=repo,
        reindex=True,
        with_plan=False,
    )
    names = [s.get("name") for s in (payload["impact"]["result"].get("symbols_in_hunks") or [])]
    assert "Person" in names, names
    assert "UserController" in payload["markdown"]


def test_pr_gate_petclinic_person_hunk_names_controllers(tmp_path: Path) -> None:
    if not PETCLINIC.is_dir():
        pytest.skip("clone spring-petclinic per benchmarks/ground-truth/blind-pack/CLONE.md")
    wt = tmp_path / "pc"
    subprocess.run(
        [
            "git",
            "-C",
            str(PETCLINIC),
            "worktree",
            "add",
            "--detach",
            str(wt),
            PETCLINIC_PIN,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        _git(wt, "config", "user.email", "test@example.com")
        _git(wt, "config", "user.name", "Test")
        person = (
            wt
            / "src"
            / "main"
            / "java"
            / "org"
            / "springframework"
            / "samples"
            / "petclinic"
            / "model"
            / "Person.java"
        )
        person.write_text(
            person.read_text(encoding="utf-8").replace(
                "return this.firstName;",
                'return this.firstName == null ? "" : this.firstName;',
            ),
            encoding="utf-8",
        )
        _git(wt, "add", "src/main/java/org/springframework/samples/petclinic/model/Person.java")
        _git(wt, "commit", "-m", "touch Person.getFirstName")
        db = tmp_path / "pc.sqlite"
        payload = run_pr_gate(
            db,
            base_ref=PETCLINIC_PIN,
            head_ref="HEAD",
            root=wt,
            reindex=True,
            with_plan=False,
        )
        md = payload["markdown"]
        names = [
            s.get("name")
            for s in (payload["impact"]["result"].get("symbols_in_hunks") or [])
        ]
        assert "Person" in names, names
        for ctl in ("OwnerController", "PetController", "VisitController"):
            assert ctl in md, md
    finally:
        subprocess.run(
            ["git", "-C", str(PETCLINIC), "worktree", "remove", "--force", str(wt)],
            capture_output=True,
            text=True,
        )
