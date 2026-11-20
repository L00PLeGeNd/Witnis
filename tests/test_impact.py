from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact, find_related_tests
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_analyze_impact_login_has_direct_caller(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = analyze_impact(db, "login")
    assert payload["status"] in {"success", "partial"}
    direct = payload["result"]["direct"]
    assert any(
        str(e.get("target")).rsplit(".", 1)[-1] == "login"
        and str(e.get("source", "")).endswith(":main")
        for e in direct
    ), direct


def test_analyze_impact_auth_service_sees_import(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = analyze_impact(db, "AuthService")
    assert payload["result"]["direct"]


def test_dedupe_collapses_qualified_alias_but_keeps_distinct_receivers() -> None:
    from witnis.core.tools import _dedupe_edges

    base = {"source": "a.py:f", "relation_type": "calls", "start_line": 3}
    rows = [
        {**base, "target": "pkg.mod.login"},
        {**base, "target": "login"},
        {**base, "target": "Owner.getName"},
        {**base, "target": "Pet.getName"},
    ]
    assert [r["target"] for r in _dedupe_edges(rows)] == [
        "pkg.mod.login",
        "Owner.getName",
        "Pet.getName",
    ]


def test_dedupe_prefers_calls_over_same_site_references() -> None:
    from witnis.core.tools import _dedupe_edges

    rows = [
        {
            "source": "verify.py:run_verification",
            "target": "witnis.core.security.redact_text",
            "relation_type": "references",
            "start_line": 449,
        },
        {
            "source": "verify.py:run_verification",
            "target": "redact_text",
            "relation_type": "calls",
            "start_line": 449,
        },
        {
            "source": "verify.py:run_verification",
            "target": "redact_text",
            "relation_type": "calls",
            "start_line": 450,
        },
    ]
    out = _dedupe_edges(rows)
    assert [(e["relation_type"], e["start_line"], e["target"]) for e in out] == [
        ("calls", 449, "witnis.core.security.redact_text"),
        ("calls", 450, "redact_text"),
    ]


def test_analyze_impact_respects_limit(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    full = analyze_impact(db, "login")
    capped = analyze_impact(db, "login", limit=1)
    assert len(full["result"]["direct"]) >= 1
    assert len(capped["result"]["direct"]) <= 1
    assert len(capped["result"]["transitive"]) <= 1


def test_is_test_path_covers_java_go_and_js_layouts() -> None:
    from witnis.core.tools import is_test_path

    for p in (
        "tests/test_auth.py",
        "src/test/java/org/x/model/ValidatorTests.java",
        "pkg/server_test.go",
        "web/src/app.spec.ts",
        "web/__tests__/button.jsx",
    ):
        assert is_test_path(p), p
    for p in ("src/main/java/org/x/Owner.java", "src/witnis/core/tools.py", "latest.py"):
        assert not is_test_path(p), p


def test_find_related_tests_finds_fixture_test(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    payload = find_related_tests(db, "login")
    assert payload["status"] == "success"
    assert any(
        "test_auth.py" in str(t.get("file_path")) for t in payload["result"]["tests"]
    ), payload["result"]["tests"]


def test_mcp_registers_impact_tools() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "impact" in names
