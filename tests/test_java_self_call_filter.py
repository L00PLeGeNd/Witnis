"""Seam: Java call extraction drops tautological self-calls (FAILURE_CASES F3)."""

from __future__ import annotations

from pathlib import Path

from witnis.core.relations_java import parse_java_calls


def test_drops_method_name_self_call(tmp_path: Path) -> None:
    src = tmp_path / "OwnerController.java"
    src.write_text(
        """
public class OwnerController {
    public OwnerController(OwnerRepository owners) {
        OwnerController(owners);
    }
    public void save() {
        save();
    }
}
""".strip(),
        encoding="utf-8",
    )
    edges = parse_java_calls(src, rel_path="OwnerController.java")
    assert not any(
        str(e.get("target") or "").endswith("save")
        or str(e.get("target") or "") == "OwnerController"
        for e in edges
    ), edges
