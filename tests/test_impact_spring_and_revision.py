"""Seams: analyze_impact (+ index revision meta).

D01/D02 — Impact must surface Spring-style injects/implements and qualified callers.
D03 — Envelope/repository must expose indexed_revision; drift → STALE limitation.
"""

from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact, repo_overview

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "fixtures" / "semantic_java_di"
AUTH = ROOT / "fixtures" / "auth_refresh"


def test_impact_finduser_includes_controller_caller(tmp_path: Path) -> None:
    db = tmp_path / "di.sqlite"
    index_repository(DI, db, incremental=False)
    payload = analyze_impact(db, target="findUser")
    direct = (payload.get("result") or {}).get("direct") or []
    assert any(
        "UserController" in str(e.get("source")) for e in direct
    ), direct


def test_impact_userrepository_includes_injects_and_implements(tmp_path: Path) -> None:
    db = tmp_path / "di2.sqlite"
    index_repository(DI, db, incremental=False)
    payload = analyze_impact(db, target="UserRepository")
    direct = (payload.get("result") or {}).get("direct") or []
    types = {str(e.get("relation_type")) for e in direct}
    assert "injects" in types, direct
    assert "implements" in types, direct
    assert any("UserService" in str(e.get("source")) for e in direct), direct
    assert any("JdbcUserRepository" in str(e.get("source")) for e in direct), direct


def test_impact_refresh_token_includes_controller_and_filter(tmp_path: Path) -> None:
    db = tmp_path / "auth.sqlite"
    index_repository(AUTH, db, incremental=False)
    payload = analyze_impact(db, target="refresh_token")
    direct = (payload.get("result") or {}).get("direct") or []
    blob = " ".join(str(e.get("source")) for e in direct)
    assert "controller" in blob.lower() or "AuthController" in blob, direct
    assert "filter" in blob.lower() or "AuthFilter" in blob, direct


def test_overview_exposes_indexed_revision(tmp_path: Path) -> None:
    db = tmp_path / "rev.sqlite"
    index_repository(DI, db, incremental=False)
    overview = repo_overview(db)
    repo = (overview.get("repository") or {})
    # fixtures live inside Witnis git → should capture a sha or workdir marker
    assert repo.get("indexed_revision"), repo
    assert overview.get("result", {}).get("indexed_revision") or repo.get(
        "indexed_revision"
    )


def test_impact_marks_stale_when_indexed_revision_set_and_forced_mismatch(
    tmp_path: Path, monkeypatch
) -> None:
    db = tmp_path / "stale.sqlite"
    index_repository(DI, db, incremental=False)
    # Force stored revision to nonsense so live HEAD cannot match
    from witnis.core.store import Store

    store = Store(db)
    try:
        store.conn.execute(
            "UPDATE repositories SET indexed_revision = ? WHERE id = ("
            "SELECT id FROM repositories ORDER BY id DESC LIMIT 1)",
            ("deadbeef-not-a-real-head",),
        )
        store.conn.commit()
    finally:
        store.close()
    payload = analyze_impact(db, target="findUser")
    limitations = " ".join(payload.get("limitations") or [])
    assert "STALE" in limitations.upper() or "stale" in limitations.lower(), limitations
    statuses = {e.get("status") for e in (payload.get("evidence") or [])}
    # at least one stale marker or limitation is required
    assert "stale" in statuses or "STALE" in limitations.upper()
