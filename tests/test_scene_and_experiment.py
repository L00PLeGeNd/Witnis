from __future__ import annotations

from pathlib import Path

from witnis.core.ab_experiment import run_pack
from witnis.core.scene import format_scene_text, run_scene

ROOT = Path(__file__).resolve().parents[1]


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
