from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.ab_experiment import run_pack
from witnis.core.scene import format_scene_text, render_browser_demo, run_scene

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_scene_auth_refresh_story(tmp_path: Path) -> None:
    payload = run_scene(
        ROOT,
        fixture_rel="fixtures/auth_refresh",
        symbol="refresh_token",
        db_path=tmp_path / "scene.sqlite",
    )
    assert payload["status"] == "success"
    story = payload["story"]
    assert story["2_context"]["indexed_symbols"] >= 1
    assert story["3_impact"]["direct_edges"] >= 1
    text = format_scene_text(payload)
    assert "Impact" in text
    assert "Why this is not" in text
    assert "transitive" in text


def test_scene_java_person_sample_includes_controller(tmp_path: Path) -> None:
    payload = run_scene(
        ROOT,
        fixture_rel="fixtures/semantic_java_di",
        symbol="Person",
        task="Change Person without missing typed users",
        db_path=tmp_path / "scene.sqlite",
    )
    assert payload["status"] == "success"
    blob = str(payload["story"]["3_impact"])
    assert "UserController" in blob
    text = format_scene_text(payload)
    assert "UserController" in text


def test_browser_demo_html_contains_story(tmp_path: Path) -> None:
    payload = run_scene(
        ROOT,
        fixture_rel="fixtures/auth_refresh",
        symbol="refresh_token",
        db_path=tmp_path / "scene.sqlite",
    )
    out = tmp_path / "browser-demo.html"
    demo = render_browser_demo(payload, out=out)
    assert demo["status"] == "success"
    html = out.read_text(encoding="utf-8")
    assert "Witnis" in html
    assert "refresh" in html.lower()
    assert "prefers-reduced-motion" in html
    assert "transitive" in html
    assert "__WITNIS_SCENE__" not in html


def test_browser_demo_cli_no_open(tmp_path: Path) -> None:
    out = tmp_path / "cli-demo.html"
    result = runner.invoke(
        app,
        ["browser-demo", "--no-open", "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    assert "browser_demo" in result.output or out.name in result.output


def test_ab_pack_witnis_beats_or_ties_caller_recall(tmp_path: Path) -> None:
    report = run_pack(
        ROOT,
        ROOT / "benchmarks" / "experiments" / "ab_analysis_pack.json",
        tmp_path,
    )
    assert report["results"]
    for row in report["results"]:
        if row.get("skipped"):
            continue
        a = row.get("caller_recall_a")
        b = row.get("caller_recall_b")
        if a is None or b is None:
            continue
        assert b >= a, row


def test_run_pack_skips_missing_corpus(tmp_path: Path) -> None:
    pack = tmp_path / "pack.json"
    pack.write_text(
        '{"id":"skip-test","tasks":[{"id":"gone","corpus":"no/such/tree","needle":"X",'
        '"expect_callers_substr":["Nope"]}]}',
        encoding="utf-8",
    )
    report = run_pack(ROOT, pack, tmp_path / "work")
    assert report["results"][0]["skipped"] is True
    assert "no/such/tree" in report["results"][0]["reason"]


def test_petclinic_person_impact_finds_controllers_grep_misses(tmp_path: Path) -> None:
    checkout = ROOT / "benchmarks" / "ground-truth" / "corpora" / "checkouts" / "spring-petclinic"
    if not checkout.is_dir():
        pytest.skip("clone spring-petclinic per benchmarks/ground-truth/blind-pack/CLONE.md")
    report = run_pack(
        ROOT,
        ROOT / "benchmarks" / "experiments" / "ab_analysis_pack.json",
        tmp_path,
    )
    row = next(r for r in report["results"] if r["task_id"] == "petclinic-person-impact")
    assert not row.get("skipped"), row
    assert row["caller_recall_a"] == 0.0, row["arm_a"]["callers_found"]
    assert row["caller_recall_b"] == 1.0, row["arm_b"]["callers_found"]
