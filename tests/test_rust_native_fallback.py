from __future__ import annotations

from pathlib import Path

from witnis.core.discover import iter_source_files
from witnis.core.index import index_repository
from witnis.core.native import (
    NATIVE_AVAILABLE,
    rust_index_repository,
    rust_list_source_files,
    rust_parse_shallow,
    rust_scan_digests,
    rust_search,
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
    stats = index_repository(ROOT / "fixtures" / "mini_go", db, incremental=False)
    assert stats.files >= 1
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


def test_rust_index_env_opt_in_for_python(tmp_path: Path, monkeypatch) -> None:
    import os

    monkeypatch.setenv("WITNIS_RUST_INDEX", "1")
    if not NATIVE_AVAILABLE:
        return
    db = tmp_path / "py-rust.sqlite"
    stats = index_repository(ROOT / "fixtures" / "mini_py", db, incremental=False)
    assert stats.symbols >= 1
    store = Store(db)
    try:
        hits = store.search("login", limit=20)
        assert hits, hits
        assert any(
            h["name"] in {"login", "AuthService.login", "SecureAuth.login"}
            or "login" in h["name"].lower()
            for h in hits
        ), hits
    finally:
        store.close()
    os.environ.pop("WITNIS_RUST_INDEX", None)


def test_rust_python_parse_shallow_methods() -> None:
    if not NATIVE_AVAILABLE:
        return
    source = (ROOT / "fixtures" / "mini_py" / "auth.py").read_text(encoding="utf-8")
    parsed = rust_parse_shallow("python", source, "auth.py")
    assert parsed is not None
    symbols, relations = parsed
    assert any(s["name"] == "AuthService.login" and s["kind"] == "method" for s in symbols)
    assert any(r["relation_type"] == "inherits" for r in relations)
    assert any(r["relation_type"] == "decorated_by" for r in relations)


def test_rust_search_after_index(tmp_path: Path) -> None:
    if not NATIVE_AVAILABLE:
        return
    db = tmp_path / "search.sqlite"
    stats = rust_index_repository(ROOT / "fixtures" / "mini_go", db, incremental=False)
    assert stats is not None
    hits = rust_search(db, "Login", limit=10)
    assert hits is not None
    assert any(h["name"] == "Login" for h in hits), hits


def test_public_svc_indexes_polyglot(tmp_path: Path) -> None:
    db = tmp_path / "public_svc.sqlite"
    stats = index_repository(ROOT / "fixtures" / "public_svc", db, incremental=False)
    assert stats.files >= 12
    assert stats.symbols >= 18
    store = Store(db)
    try:
        hits = store.search("charge", limit=20)
        assert any(
            h["name"] in {"BillingService.charge", "PromoBilling.charge", "charge"}
            for h in hits
        ), hits
        assert any(h["name"] == "Issue" for h in store.search("Issue", limit=20))
        assert any(h["name"] == "BillingClient" for h in store.search("BillingClient", limit=20))
    finally:
        store.close()


def test_lsp_index_fallback_without_requiring_jedi(tmp_path: Path) -> None:
    from witnis.core.tools import query_lsp

    db = tmp_path / "lsp.sqlite"
    index_repository(ROOT / "fixtures" / "mini_py", db, incremental=False)
    payload = query_lsp(db, "AuthService", limit=10)
    result = payload.get("result") or {}
    assert result.get("available") is True
    assert result.get("definitions") or result.get("references")
    assert "index" in str(result.get("backend") or "") or result.get("definitions")
