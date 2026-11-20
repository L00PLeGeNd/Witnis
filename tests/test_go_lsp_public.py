from __future__ import annotations

from pathlib import Path

from witnis.bench import run_benchmark
from witnis.core.index import index_repository
from witnis.core.lsp_python import lsp_available
from witnis.core.store import Store
from witnis.core.tools import list_capabilities, query_lsp
from witnis.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_GO = ROOT / "fixtures" / "mini_go"
FIXTURE_JAVA = ROOT / "fixtures" / "mini_java"
FIXTURE_PY = ROOT / "fixtures" / "mini_py"


def test_indexes_go_symbols_and_imports(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_GO, db, incremental=False)
    store = Store(db)
    try:
        overview = store.overview()
        assert overview["symbols"] >= 3
        hits = store.search("Login", limit=10)
        assert any(h["name"] == "Login" for h in hits), hits
        imports = store.find_relations(relation_type="imports", limit=50)
        assert any("auth" in str(e.get("target")) for e in imports), imports
        calls = store.find_relations(relation_type="calls", limit=50)
        assert any("Login" in str(e.get("target")) for e in calls), calls
    finally:
        store.close()


def test_indexes_java_symbols_and_imports(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JAVA, db, incremental=False)
    store = Store(db)
    try:
        hits = store.search("login", limit=20)
        assert any(h["name"] == "login" for h in hits), hits
        imports = store.find_relations(relation_type="imports", limit=50)
        assert any("AuthService" in str(e.get("target")) for e in imports), imports
    finally:
        store.close()


def test_query_lsp_graceful_without_or_with_jedi(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    payload = query_lsp(db, "AuthService")
    assert payload["status"] in {"success", "partial"}
    assert "available" in payload["result"]
    if lsp_available():
        assert payload["result"]["definitions"] or payload["result"]["references"]
    else:
        assert any("witnis[lsp]" in x for x in payload.get("limitations") or [])


def test_public_benchmark_suite(tmp_path: Path) -> None:
    report = run_benchmark(
        ROOT,
        ROOT / "benchmarks" / "public" / "tasks.json",
        tmp_path / "public-bench.sqlite",
    )
    assert report["total"] >= 8
    assert report["passed"] == report["total"], report


def test_capabilities_include_lsp_and_go_surface() -> None:
    payload = list_capabilities()
    assert "lsp" in payload["result"]["cli_commands"]
    assert "query_lsp" in payload["result"]["mcp_experimental"]
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "query_lsp" in names
