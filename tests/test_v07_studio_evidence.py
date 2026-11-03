from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import get_evidence, list_capabilities, refresh_evidence, refresh_index
from witnis.core.verify import run_verification
from witnis.mcp_server import build_server
from witnis.studio import render_studio

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "mini_py"


def test_refresh_evidence_marks_stale_after_file_change(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    target = repo / "auth.py"
    target.write_text(
        "class AuthService:\n    def login(self, u: str) -> bool:\n        return True\n",
        encoding="utf-8",
    )
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)

    before = get_evidence(db, "login", status="verified")
    assert before["result"]["stored_count"] >= 1

    target.write_text(
        "class AuthService:\n    def login(self, u: str) -> bool:\n        return False\n",
        encoding="utf-8",
    )
    # Incremental refresh also runs evidence freshness
    refreshed = refresh_index(db)
    assert int((refreshed.get("result") or {}).get("evidence_marked_stale") or 0) >= 1

    payload = refresh_evidence(db)
    assert payload["status"] == "success"

    stale = get_evidence(db, "login", status="stale")
    assert stale["result"]["stored_count"] >= 1


def test_studio_embeds_graph_evidence_report(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    out = tmp_path / "studio.html"
    payload = render_studio(db, out=out, target="login", lang="en")
    assert payload["status"] == "success"
    html = out.read_text(encoding="utf-8")
    assert "flowchart LR" in html or "relation graph" in html.lower() or "Graph" in html
    assert "Evidence" in html
    assert "Report" in html
    assert "__WITNIS_DATA__" not in html
    result = payload["result"]
    assert result.get("has_graph") is True
    assert result.get("has_report") is True


def test_studio_zh_labels(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    out = tmp_path / "studio-zh.html"
    render_studio(db, out=out, target="login", lang="zh")
    html = out.read_text(encoding="utf-8")
    assert "证据" in html or "验证" in html or "索引" in html


def test_sdk_exports() -> None:
    import witnis.sdk as sdk

    assert callable(sdk.index_repository)
    assert callable(sdk.repo_search)
    assert callable(sdk.render_studio)
    assert callable(sdk.refresh_evidence)


def test_capabilities_and_mcp_v07() -> None:
    payload = list_capabilities()
    assert "refresh-evidence" in payload["result"]["cli_commands"]
    assert "refresh_evidence" in payload["result"]["mcp_tools"]
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "refresh_evidence" in names


def test_store_can_update_evidence_status(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    store = Store(db)
    try:
        overview = store.overview()
        repo_id = int(overview["repository"]["id"])
        store.insert_evidence_items(
            repo_id,
            [
                {
                    "type": "manual",
                    "status": "observed",
                    "path": "auth.py",
                    "source_ref": "login",
                    "content_hash": "deadbeef",
                }
            ],
        )
        rows = store.find_evidence(query="login", limit=10)
        assert rows
        n = store.mark_evidence_status([int(rows[0]["id"])], "stale")
        assert n == 1
        assert store.find_evidence(status="stale", limit=5)
    finally:
        store.close()
