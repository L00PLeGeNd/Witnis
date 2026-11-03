from __future__ import annotations

from pathlib import Path

from witnis.compare_baselines import run_baseline_compare
from witnis.core.tools import list_capabilities
from witnis import __version__

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "mini_py"


def test_baseline_compare_beats_grep_on_structure(tmp_path: Path) -> None:
    report = run_baseline_compare(FIXTURE, tmp_path / "cmp.sqlite")
    assert report["status"] == "success"
    result = report["result"]
    assert result["witnis"]["search_hits"] >= 1
    assert result["witnis"]["trace_callers"] >= 1
    assert result["witnis"]["impact_direct"] >= 1
    assert result["baselines"]["git_grep"]["hit_count"] >= 1
    # Grep finds text; Witnis additionally returns typed symbols / relations
    assert result["deltas"]["typed_symbols_over_grep"] >= 1
    assert result["deltas"]["relation_edges_over_grep"] >= 1
    assert result["security"]["verify_blocked_without_auth"] is True
    assert result["security"]["unauthorized_writes"] == 0
    assert "markdown" in result
    assert "Witnis vs baselines" in result["markdown"]


def test_version_is_v1() -> None:
    assert __version__.startswith("1.")


def test_capabilities_mark_stable_core() -> None:
    payload = list_capabilities()
    result = payload["result"]
    assert result["contract"] == "stable"
    assert "repo_search" in result["stable_mcp_tools"]
    assert "run_verification" in result["stable_mcp_tools"]
    assert "index" in result["stable_cli_commands"]
