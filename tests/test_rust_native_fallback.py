from __future__ import annotations

from pathlib import Path

from witnis.core.discover import iter_source_files
from witnis.core.index import index_repository
from witnis.core.native import (
    NATIVE_AVAILABLE,
    rust_list_source_files,
    rust_parse_shallow,
    rust_scan_digests,
)
from witnis.core.store import Store

ROOT = Path(__file__).resolve().parents[1]


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
        root = ROOT / "fixtures" / "mini_py"
        rels = rust_list_source_files(root)
        assert rels is not None
        assert any(r.endswith("auth.py") for r in rels)
        digests = rust_scan_digests(root)
        assert digests and all("sha256" in d for d in digests)
        source = (ROOT / "fixtures" / "mini_go" / "auth.go").read_text(encoding="utf-8")
        parsed = rust_parse_shallow("go", source, "auth.go")
        assert parsed is not None
        symbols, _relations = parsed
        assert any(s["name"] == "Login" for s in symbols)


def test_index_go_java_still_works(tmp_path: Path) -> None:
    db = tmp_path / "go.sqlite"
    index_repository(ROOT / "fixtures" / "mini_go", db, incremental=False)
    store = Store(db)
    try:
        assert any(h["name"] == "Login" for h in store.search("Login", limit=10))
    finally:
        store.close()
    db2 = tmp_path / "java.sqlite"
    index_repository(ROOT / "fixtures" / "mini_java", db2, incremental=False)
    store = Store(db2)
    try:
        assert any(h["name"] == "login" for h in store.search("login", limit=20))
    finally:
        store.close()
