from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from witnis.core.index import index_repository
from witnis.core.tools import (
    analyze_impact,
    check_import_graph,
    check_index_health,
    explain_code,
    export_evidence_bundle,
    find_related_tests,
    get_evidence,
    export_relation_graph,
    list_capabilities,
    list_index_snapshots,
    ingest_runtime_traces,
    query_lsp,
    refresh_evidence,
    render_evidence_report,
    repo_overview,
    repo_search,
    repo_status,
    trace_symbol,
)
from witnis.compare_baselines import run_baseline_compare
from witnis.core.verify import create_verification_plan, run_verification
from witnis.studio import render_studio


@dataclass
class TaskResult:
    id: str
    passed: bool
    detail: str


def _load_tasks(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_expect(kind: str, payload: dict[str, Any], expect: dict[str, Any]) -> tuple[bool, str]:
    if kind == "search":
        names = {m.get("name") for m in payload.get("result", {}).get("matches", [])}
        wanted = set(expect.get("any_symbol_names") or [])
        ok = bool(names & wanted)
        return ok, f"names={sorted(names)}"

    if kind == "trace":
        called_by = payload.get("result", {}).get("called_by") or []
        suffixes = expect.get("called_by_source_suffix") or []
        deco_targets = expect.get("decorated_by_target") or []
        if deco_targets:
            deco = payload.get("result", {}).get("decorated_by") or []
            ok = any(
                any(str(edge.get("target")) == t for t in deco_targets) for edge in deco
            )
            return ok, f"decorated_by={deco}"
        ok = any(
            any(str(edge.get("source", "")).endswith(suf) for suf in suffixes)
            for edge in called_by
        )
        return ok, f"called_by={called_by}"

    if kind == "impact":
        direct = payload.get("result", {}).get("direct") or []
        suffixes = expect.get("direct_source_suffix") or []
        ok = any(
            any(str(edge.get("source", "")).endswith(suf) for suf in suffixes)
            for edge in direct
        )
        return ok, f"direct={direct}"

    if kind == "related_tests":
        tests = payload.get("result", {}).get("tests") or []
        needles = expect.get("test_file_contains") or []
        ok = any(
            any(n in str(t.get("file_path")) for n in needles) for t in tests
        )
        return ok, f"tests={tests}"

    if kind == "evidence":
        count = len(payload.get("evidence") or [])
        need = int(expect.get("min_evidence") or 1)
        return count >= need, f"evidence_count={count}"

    if kind == "overview":
        result = payload.get("result") or {}
        ok = (
            int(result.get("symbols") or 0) >= int(expect.get("min_symbols") or 0)
            and int(result.get("files") or 0) >= int(expect.get("min_files") or 0)
        )
        return ok, f"files={result.get('files')} symbols={result.get('symbols')}"

    if kind == "overview_relations":
        sample = payload.get("result", {}).get("relation_sample") or []
        needles = expect.get("relation_target_contains") or []
        ok = any(any(n in str(e.get("target")) for n in needles) for e in sample)
        return ok, f"relations={sample}"

    if kind == "plan_verify":
        steps = payload.get("result", {}).get("steps") or []
        kinds = {s.get("kind") for s in steps}
        wanted = set(expect.get("step_kinds") or [])
        ok = wanted.issubset(kinds)
        return ok, f"step_kinds={sorted(kinds)}"

    if kind == "verify_blocked":
        state = payload.get("result", {}).get("state")
        ok = state == expect.get("state")
        return ok, f"state={state}"

    if kind == "explain_code":
        snippet = payload.get("result", {}).get("snippet") or []
        need = int(expect.get("min_snippet_lines") or 1)
        ok = len(snippet) >= need
        return ok, f"snippet_lines={len(snippet)}"

    if kind == "mcp_tools":
        names = set(payload.get("result", {}).get("tools") or [])
        wanted = set(expect.get("tool_names") or [])
        ok = wanted.issubset(names)
        return ok, f"tools={sorted(names)}"

    if kind == "import_graph":
        broken = int(payload.get("result", {}).get("broken_count") or 0)
        max_broken = int(expect.get("max_broken") or 0)
        ok = broken <= max_broken
        return ok, f"broken_count={broken}"

    if kind == "export_bundle":
        bundle = payload.get("result", {}).get("bundle") or {}
        wanted = set(expect.get("bundle_keys") or [])
        ok = wanted.issubset(set(bundle.keys()))
        return ok, f"bundle_keys={sorted(bundle.keys())}"

    if kind == "index_health":
        issues = payload.get("result", {}).get("issues") or []
        max_issues = int(expect.get("max_issues") or 0)
        ok = len(issues) <= max_issues
        return ok, f"issues={issues}"

    if kind == "report":
        md = payload.get("result", {}).get("markdown") or ""
        needles = expect.get("markdown_contains") or []
        ok = all(n in md for n in needles)
        return ok, f"markdown_len={len(md)}"

    if kind == "status":
        result = payload.get("result") or {}
        wanted = set(expect.get("has_keys") or [])
        ok = wanted.issubset(set(result.keys()))
        return ok, f"keys={sorted(result.keys())}"

    if kind == "snapshots":
        count = int(payload.get("result", {}).get("count") or 0)
        need = int(expect.get("min_count") or 1)
        ok = count >= need
        return ok, f"count={count}"

    if kind == "graph":
        graph = payload.get("result", {}).get("graph") or ""
        needles = expect.get("graph_contains") or []
        min_edges = int(expect.get("min_edges") or 0)
        edges = int(payload.get("result", {}).get("edge_count") or 0)
        ok = all(n in graph for n in needles) and edges >= min_edges
        return ok, f"edges={edges}"

    if kind == "capabilities":
        tools = payload.get("result", {}).get("mcp_tools") or []
        experimental = payload.get("result", {}).get("mcp_experimental") or []
        need = int(expect.get("min_mcp_tools") or 1)
        ok = len(tools) >= need
        exact = expect.get("exact_mcp_tools")
        if exact:
            ok = ok and set(tools) == set(exact)
        min_exp = expect.get("min_mcp_experimental")
        if min_exp is not None:
            ok = ok and len(experimental) >= int(min_exp)
        return ok, f"mcp_tools={len(tools)} experimental={len(experimental)}"

    if kind == "studio":
        result = payload.get("result") or {}
        ok = True
        if expect.get("has_graph") is True:
            ok = ok and bool(result.get("has_graph"))
        if expect.get("has_report") is True:
            ok = ok and bool(result.get("has_report"))
        return ok, f"studio={result}"

    if kind == "refresh_evidence":
        result = payload.get("result") or {}
        checked = int(result.get("checked") or 0)
        need = int(expect.get("min_checked") or 0)
        ok = payload.get("status") in {"success", "partial"} and checked >= need
        return ok, f"checked={checked} stale={result.get('marked_stale')}"

    if kind == "ingest_traces":
        result = payload.get("result") or {}
        accepted = int(result.get("accepted") or 0)
        need = int(expect.get("min_accepted") or 1)
        ok = payload.get("status") == "success" and accepted >= need
        return ok, f"accepted={accepted} added={result.get('relations_added')}"

    if kind == "baselines":
        result = payload.get("result") or {}
        deltas = result.get("deltas") or {}
        security = result.get("security") or {}
        ok = (
            int(deltas.get("typed_symbols_over_grep") or 0)
            >= int(expect.get("min_typed_symbols") or 1)
            and int(deltas.get("relation_edges_over_grep") or 0)
            >= int(expect.get("min_relation_edges") or 1)
        )
        if expect.get("verify_blocked") is True:
            ok = ok and bool(security.get("verify_blocked_without_auth"))
        return ok, f"deltas={deltas} security={security}"

    if kind in {"go_search", "fixture_search", "js_search", "java_search"}:
        names = {m.get("name") for m in payload.get("result", {}).get("matches", [])}
        wanted = set(expect.get("any_symbol_names") or [])
        ok = bool(names & wanted)
        return ok, f"names={sorted(names)}"

    if kind == "lsp":
        result = payload.get("result") or {}
        if expect.get("allow_unavailable") and not result.get("available"):
            return True, "lsp_unavailable_allowed"
        ok = bool(result.get("definitions") or result.get("references"))
        return ok, f"lsp={result}"

    if kind == "overview_min":
        result = payload.get("result") or {}
        ok = (
            int(result.get("files") or 0) >= int(expect.get("min_files") or 0)
            and int(result.get("symbols") or 0) >= int(expect.get("min_symbols") or 0)
        )
        return ok, f"files={result.get('files')} symbols={result.get('symbols')}"

    return False, f"unknown kind={kind}"


def run_benchmark(
    repo_root: Path,
    tasks_path: Path,
    db_path: Path,
) -> dict[str, Any]:
    spec = _load_tasks(tasks_path)
    fixture_rel = spec.get("fixture") or "fixtures/mini_py"
    fixture = (repo_root / fixture_rel).resolve()
    index_repository(fixture, db_path, incremental=False)

    results: list[TaskResult] = []
    for task in spec.get("tasks") or []:
        kind = task["kind"]
        query = task.get("query") or ""
        expect = task.get("expect") or {}
        if kind == "search":
            payload = repo_search(db_path, query)
        elif kind == "trace":
            payload = trace_symbol(db_path, query)
        elif kind == "impact":
            payload = analyze_impact(db_path, query)
        elif kind == "related_tests":
            payload = find_related_tests(db_path, query)
        elif kind == "evidence":
            payload = get_evidence(db_path, query)
        elif kind in {"overview", "overview_relations"}:
            payload = repo_overview(db_path)
        elif kind == "plan_verify":
            payload = create_verification_plan(db_path, target=query or None)
        elif kind == "verify_blocked":
            payload = run_verification(db_path, execute=False, target=query or None)
        elif kind == "explain_code":
            payload = explain_code(db_path, query)
        elif kind == "mcp_tools":
            from witnis.mcp_server import build_server

            payload = {
                "result": {
                    "tools": [t.name for t in build_server()._tool_manager.list_tools()]
                }
            }
        elif kind == "import_graph":
            payload = check_import_graph(db_path)
        elif kind == "export_bundle":
            payload = export_evidence_bundle(db_path, target=query or None)
        elif kind == "index_health":
            payload = check_index_health(db_path)
        elif kind == "report":
            payload = render_evidence_report(db_path, target=query or None)
        elif kind == "status":
            payload = repo_status(db_path)
        elif kind == "snapshots":
            payload = list_index_snapshots(db_path)
        elif kind == "graph":
            payload = export_relation_graph(db_path, query or "login", fmt="mermaid")
        elif kind == "capabilities":
            payload = list_capabilities()
        elif kind == "studio":
            out = db_path.parent / "bench-studio.html"
            payload = render_studio(db_path, out=out, target=query or "login")
        elif kind == "refresh_evidence":
            payload = refresh_evidence(db_path)
        elif kind == "ingest_traces":
            rel = query or "fixtures/mini_py/sample_trace.jsonl"
            payload = ingest_runtime_traces(db_path, (repo_root / rel).resolve())
        elif kind == "baselines":
            payload = run_baseline_compare(
                (repo_root / (spec.get("fixture") or "fixtures/mini_py")).resolve(),
                db_path,
                query=query or "login",
            )
        elif kind == "go_search":
            go_db = db_path.parent / "bench-go.sqlite"
            index_repository(
                (repo_root / "fixtures" / "mini_go").resolve(),
                go_db,
                incremental=False,
            )
            payload = repo_search(go_db, query or "Login")
        elif kind in {"fixture_search", "js_search", "java_search"}:
            fixture_rel = (
                task.get("fixture")
                or expect.get("fixture")
                or {
                    "js_search": "fixtures/mini_js",
                    "java_search": "fixtures/mini_java",
                    "fixture_search": "fixtures/public_svc",
                }.get(kind, "fixtures/public_svc")
            )
            alt_db = db_path.parent / f"bench-{kind}.sqlite"
            index_repository(
                (repo_root / fixture_rel).resolve(),
                alt_db,
                incremental=False,
            )
            payload = repo_search(alt_db, query)
        elif kind == "overview_min":
            fixture_rel = task.get("fixture") or "fixtures/public_svc"
            alt_db = db_path.parent / "bench-overview.sqlite"
            index_repository(
                (repo_root / fixture_rel).resolve(),
                alt_db,
                incremental=False,
            )
            payload = repo_overview(alt_db)
        elif kind == "lsp":
            payload = query_lsp(db_path, query or "AuthService")
        else:
            results.append(TaskResult(task["id"], False, f"unsupported kind {kind}"))
            continue
        ok, detail = _check_expect(kind, payload, expect)
        results.append(TaskResult(task["id"], ok, detail))

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    return {
        "fixture": str(fixture),
        "passed": passed,
        "total": total,
        "score": (passed / total) if total else 0.0,
        "results": [{"id": r.id, "passed": r.passed, "detail": r.detail} for r in results],
    }
