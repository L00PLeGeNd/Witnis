from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import analyze_impact, list_capabilities, refresh_index
from witnis.mcp_server import build_server
from witnis.studio import render_studio

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PY = ROOT / "fixtures" / "mini_py"
FIXTURE_JS = ROOT / "fixtures" / "mini_js"


def test_indexes_js_extends_inherits(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JS, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="inherits", limit=50)
    finally:
        store.close()
    assert any(
        str(e.get("source", "")).endswith("CachingTokenService")
        and e.get("target") == "TokenService"
        for e in edges
    ), edges


def test_js_impact_includes_subclass(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JS, db, incremental=False)
    payload = analyze_impact(db, "TokenService")
    direct = payload["result"]["direct"]
    assert any(
        e.get("relation_type") == "inherits"
        and str(e.get("source", "")).endswith("CachingTokenService")
        for e in direct
    ), direct


def test_render_studio_writes_html(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    out = tmp_path / "studio.html"
    payload = render_studio(db, out=out)
    assert payload["status"] == "success"
    assert out.is_file()
    html = out.read_text(encoding="utf-8")
    assert "Witnis" in html
    assert "witnis-data" in html
    assert "__WITNIS_DATA__" not in html
    assert "mini_py" in html or "files" in html


def test_watch_one_cycle(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    # Direct refresh is what watch loops on
    payload = refresh_index(db)
    assert payload["status"] in {"success", "partial"}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "witnis",
            "watch",
            "--db",
            str(db),
            "--cycles",
            "1",
            "--interval",
            "1",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "updated=" in proc.stdout


def test_capabilities_include_studio_watch() -> None:
    payload = list_capabilities()
    cli = payload["result"]["cli_commands"]
    mcp = payload["result"]["mcp_experimental"]
    assert "studio" in cli
    assert "watch" in cli
    assert "render_studio" in mcp


def test_mcp_registers_studio() -> None:
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "render_studio" in names
