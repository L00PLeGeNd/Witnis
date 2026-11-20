from __future__ import annotations

import json
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.tools import get_evidence, ingest_runtime_traces, list_capabilities
from witnis.mcp_server import build_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_ingest_runtime_traces_creates_observed_edges(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    trace = tmp_path / "trace.jsonl"
    rows = [
        {"caller": "app.py:main", "callee": "AuthService.login", "ts": 1},
        {"caller": "gate.py:AccessGate.allow", "callee": "login", "count": 3},
        {"event": "call", "from": "test_auth.py:test_login_ok", "to": "AuthService.login"},
    ]
    trace.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    payload = ingest_runtime_traces(db, trace)
    assert payload["status"] == "success"
    assert payload["result"]["accepted"] >= 2
    assert payload["result"]["relations_added"] >= 2

    evidence = get_evidence(db, "login", status="observed")
    assert any(
        e.get("type") == "runtime_trace" for e in evidence.get("evidence") or []
    ), evidence


def test_capabilities_include_ingest_traces() -> None:
    payload = list_capabilities()
    assert "ingest-traces" in payload["result"]["cli_commands"]
    assert "ingest_runtime_traces" in payload["result"]["mcp_experimental"]
    names = {t.name for t in build_server()._tool_manager.list_tools()}
    assert "ingest_runtime_traces" in names
