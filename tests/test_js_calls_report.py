from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import render_evidence_report

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_JS = ROOT / "fixtures" / "mini_js"
FIXTURE_PY = ROOT / "fixtures" / "mini_py"


def test_indexes_js_calls(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JS, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="calls", limit=100)
    finally:
        store.close()
    targets = {e.get("target") for e in edges}
    assert "TokenService" in targets or any(
        str(t).endswith("issue") or str(t).endswith("verifyToken") for t in targets
    ), targets


def test_render_evidence_report_markdown(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    payload = render_evidence_report(db, target="login")
    md = payload["result"]["markdown"]
    assert "# Witnis evidence report" in md
    assert "login" in md.lower() or "AuthService" in md
    assert "##" in md
