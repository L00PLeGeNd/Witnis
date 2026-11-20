"""Seam: call-follow transitive edges are marked uncertain (FAILURE_CASES F4)."""

from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact

ROOT = Path(__file__).resolve().parents[1]


def test_call_follow_transitive_marked_uncertain(tmp_path: Path) -> None:
    db = tmp_path / "mini.sqlite"
    index_repository(ROOT / "fixtures" / "mini_py", db, incremental=False)
    payload = analyze_impact(db, "login")
    transitive = payload["result"].get("transitive") or []
    for edge in transitive:
        if edge.get("relation_type") == "calls":
            assert edge.get("status") == "uncertain", edge
