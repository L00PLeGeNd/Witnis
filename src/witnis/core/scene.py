"""Narrative scene reports — engineering outcomes, not MCP tool catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact, find_related_tests, repo_search, trace_symbol
from witnis.core.verify import create_verification_plan, run_verification

_SCENE_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "studio" / "scene_template.html"
)


DEFAULT_SCENE = {
    "id": "auth_token_refresh",
    "task": "Modify token refresh so expired refresh tokens are rejected",
    "fixture": "fixtures/auth_refresh",
    "symbol": "refresh_token",
}


def run_scene(
    repo_root: Path,
    *,
    fixture_rel: str = "fixtures/auth_refresh",
    symbol: str = "refresh_token",
    task: str = DEFAULT_SCENE["task"],
    execute_verify: bool = False,
    db_path: Path | None = None,
) -> dict[str, Any]:
    fixture = (repo_root / fixture_rel).resolve()
    if not fixture.is_dir():
        return {"status": "failed", "error": f"fixture missing: {fixture}"}

    db = db_path or (repo_root / ".witnis" / "scene.sqlite")
    db.parent.mkdir(parents=True, exist_ok=True)
    stats = index_repository(fixture, db, incremental=False)

    search = repo_search(db, query=symbol, limit=10)
    trace = trace_symbol(db, name=symbol)
    impact = analyze_impact(db, target=symbol)
    tests = find_related_tests(db, target=symbol)
    plan = create_verification_plan(db, target=symbol)

    matches = (search.get("result") or {}).get("matches") or []
    defs = (trace.get("result") or {}).get("definitions") or []
    callers = (trace.get("result") or {}).get("called_by") or []
    direct = (impact.get("result") or {}).get("direct") or []
    transitive = (impact.get("result") or {}).get("transitive") or []
    related = (tests.get("result") or {}).get("tests") or []
    steps = (plan.get("result") or {}).get("steps") or []

    verify_payload = None
    if execute_verify:
        verify_payload = run_verification(db, execute=True, target=symbol)

    story = {
        "1_task": task,
        "2_context": {
            "indexed_files": stats.files,
            "indexed_symbols": stats.symbols,
            "definitions": [
                {
                    "name": d.get("name"),
                    "file": d.get("file_path"),
                    "line": d.get("start_line"),
                    "kind": d.get("kind"),
                }
                for d in defs[:5]
            ]
            or [
                {
                    "name": m.get("name"),
                    "file": m.get("file_path"),
                    "line": m.get("start_line"),
                    "kind": m.get("kind"),
                }
                for m in matches[:5]
            ],
            "callers": [c.get("source") for c in callers[:8]],
        },
        "3_impact": {
            "direct_edges": len(direct),
            "transitive_edges": len(transitive),
            "sample": [
                {"from": e.get("source"), "to": e.get("target"), "type": e.get("relation_type")}
                for e in list(direct[:6]) + list(transitive[:6])
            ],
            "related_tests": sorted(
                {str(t.get("file_path")) for t in related if t.get("file_path")}
            ),
        },
        "4_change_guidance": [
            "Edit the refresh implementation using the definitions above — not a repo-wide text guess.",
            "Keep callers and the auth filter in the blast radius under review.",
            "Run the related tests listed under impact before claiming done.",
        ],
        "5_verification": {
            "plan_steps": [
                {"id": s.get("id"), "kind": s.get("kind"), "description": s.get("description")}
                for s in steps
            ],
            "state": (verify_payload or {}).get("result", {}).get("state")
            if verify_payload
            else "planned_only",
            "execution": (verify_payload or {}).get("result", {}).get("execution")
            if verify_payload
            else None,
            "how_to_execute": "WITNIS_ALLOW_VERIFY=1 witnis verify refresh_token --execute",
        },
    }

    return {
        "status": "success",
        "scene": "auth_token_refresh",
        "fixture": str(fixture),
        "symbol": symbol,
        "story": story,
        "why_not_bare_agent": [
            "Bare agents read files; Witnis returns typed callers, impact edges, and related tests as evidence.",
            "Verify stays gated and isolated — 'tests passed' is an explicit state, not a vibe.",
            "The user-facing artifact is this story card, not a list of MCP tool names.",
        ],
    }


def render_browser_demo(
    payload: dict[str, Any],
    *,
    out: Path | None = None,
) -> dict[str, Any]:
    """Render the auth-refresh scene story as a browser-openable HTML page."""
    if payload.get("status") != "success":
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=[str(payload.get("error") or "scene failed")],
        )
    template = _SCENE_TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False)
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e")
    html = template.replace("__WITNIS_SCENE__", blob)
    target = out or (Path.cwd() / ".witnis" / "browser-demo.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return make_envelope(
        status="success",
        repository={"name": "auth_refresh", "root_path": str(payload.get("fixture") or "")},
        result={
            "path": str(target.resolve()),
            "bytes": len(html.encode("utf-8")),
            "scene": payload.get("scene"),
            "symbol": payload.get("symbol"),
        },
        evidence=[
            {
                "type": "browser_demo",
                "status": "observed",
                "path": str(target.resolve()),
            }
        ],
        limitations=[
            "Static HTML snapshot of the scene story — not a live MCP session.",
            "Verify remains gated; opening the page does not execute tests.",
        ],
    )


def format_scene_text(payload: dict[str, Any]) -> str:
    if payload.get("status") != "success":
        return str(payload.get("error") or payload)
    story = payload["story"]
    lines = [
        "Scene: modify token refresh",
        f"Task    {story['1_task']}",
        "",
        "Context (engineering facts)",
    ]
    ctx = story["2_context"]
    lines.append(f"  index   {ctx['indexed_files']} files · {ctx['indexed_symbols']} symbols")
    for d in ctx["definitions"]:
        lines.append(f"  def     {d.get('name')}  {d.get('file')}:{d.get('line')}")
    for c in ctx["callers"]:
        lines.append(f"  caller  {c}")
    lines.append("")
    lines.append("Impact")
    imp = story["3_impact"]
    lines.append(
        f"  edges   {imp['direct_edges']} direct, "
        f"{imp.get('transitive_edges') or 0} transitive"
    )
    for e in imp["sample"][:5]:
        lines.append(f"  edge    {e.get('from')} → {e.get('to')} ({e.get('type')})")
    if imp["related_tests"]:
        lines.append(f"  tests   {', '.join(imp['related_tests'])}")
    else:
        lines.append("  tests   (none indexed)")
    lines.append("")
    lines.append("Change guidance")
    for g in story["4_change_guidance"]:
        lines.append(f"  • {g}")
    lines.append("")
    ver = story["5_verification"]
    lines.append(f"Verification  state={ver['state']}")
    for s in ver["plan_steps"][:6]:
        lines.append(f"  step    {s.get('id')}  {s.get('description')}")
    if ver["state"] == "planned_only":
        lines.append(f"  next    {ver['how_to_execute']}")
    lines.append("")
    lines.append("Why this is not 'just let the agent read the repo'")
    for w in payload.get("why_not_bare_agent") or []:
        lines.append(f"  • {w}")
    return "\n".join(lines)
