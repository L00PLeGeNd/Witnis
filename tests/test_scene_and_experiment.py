from __future__ import annotations

from pathlib import Path

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
        a = row.get("caller_recall_a")
        b = row.get("caller_recall_b")
        if a is None or b is None:
            continue
        assert b >= a, row
