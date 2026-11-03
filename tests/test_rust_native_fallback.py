from __future__ import annotations

from pathlib import Path

from witnis.core.discover import iter_source_files
from witnis.core.native import NATIVE_AVAILABLE, rust_list_source_files


def test_python_discover_works_without_native(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x=1\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "b.py").write_text("y=1\n", encoding="utf-8")
    files = iter_source_files(tmp_path)
    assert [p.name for p in files] == ["a.py"]


def test_native_helper_reports_availability() -> None:
    # Extension may or may not be built in CI; both states are valid.
    assert isinstance(NATIVE_AVAILABLE, bool)
    if NATIVE_AVAILABLE:
        root = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
        rels = rust_list_source_files(root)
        assert rels is not None
        assert any(r.endswith("auth.py") for r in rels)
