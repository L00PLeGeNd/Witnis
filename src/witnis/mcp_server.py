from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from witnis.core.tools import (
    analyze_change_impact,
    analyze_impact,
    check_import_graph,
    check_index_health,
    check_python_syntax,
    compare_revisions,
    compare_worktree,
    explain_change,
    explain_code,
    export_evidence_bundle,
    export_relation_graph,
    find_related_tests,
    get_evidence,
    list_capabilities,
    list_commits,
    list_index_snapshots,
    list_test_results,
    ingest_runtime_traces,
    query_lsp,
    refresh_evidence,
    refresh_index,
    render_evidence_report,
    repo_overview,
    repo_search,
    repo_status,
    scan_secrets,
    trace_symbol,
)
from witnis.core.verify import (
    create_verification_plan,
    get_verification_report,
    list_verification_runs,
    run_verification,
)
from witnis.studio import render_studio


def _db_path() -> Path:
    override = os.environ.get("WITNIS_DB")
    if override:
        return Path(override)
    return Path.cwd() / ".witnis" / "index.sqlite"


PUBLIC_MCP_TOOLS = ("index", "look", "impact", "verify")


def _want_experimental() -> bool:
    return os.environ.get("WITNIS_MCP_EXPERIMENTAL", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def build_server() -> FastMCP:
    server = FastMCP(
        name="witnis",
        instructions=(
            "Witnis (witnis-dev) is a local evidence gate for coding agents. "
            "Public tools: index, look, impact, verify. "
            "Never tell the user tests passed, the change is safe, or verification "
            "succeeded unless the verify tool returned automation_verified=true "
            "after an authorized execute. blocked / plan-only means 0 commands ran. "
            "Set WITNIS_MCP_EXPERIMENTAL=1 for the rest of the catalog."
        ),
    )

    def _experimental(name: str):
        """Gate non-public tools. Name avoids @tool( so static scanners count only @server.tool."""

        def deco(fn):
            if _want_experimental():
                return server.tool(name=name)(fn)
            return fn

        return deco

    from witnis.core.index import index_repository
    from witnis.core.tools import look_symbol

    @server.tool(name="index")
    def _index() -> str:
        """Index the current working directory into SQLite (WITNIS_DB or .witnis/index.sqlite). Incremental; does not run tests or modify source. Call this first in a new repo. Returns JSON with file and symbol counts."""
        db = _db_path()
        stats = index_repository(Path.cwd(), db, incremental=True)
        return json.dumps(
            {
                "status": "success",
                "result": {
                    "files": stats.files,
                    "symbols": stats.symbols,
                    "db_path": str(stats.db_path),
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    @server.tool(name="look")
    def _look(target: str) -> str:
        """Witness card for a symbol or file name: definition, callers, impact size, related tests, verify plan. Read-only. Requires a prior index. Does not execute tests."""
        return json.dumps(look_symbol(_db_path(), target), ensure_ascii=False, indent=2)

    @server.tool(name="impact")
    def _impact_public(target: str, limit: int = 50) -> str:
        """Blast-radius envelope for a symbol: direct and transitive callers/callees, capped by limit (default 50). Read-only. Requires a prior index. Not a security audit."""
        return json.dumps(
            analyze_impact(_db_path(), target=target, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @server.tool(name="verify")
    def _verify_public(target: str = "", execute: bool = False) -> str:
        """Gated verification. Default (execute=false) returns a plan only — 0 commands ran. execute=true runs tests only if WITNIS_ALLOW_VERIFY=1; otherwise status is blocked. Never treat blocked or plan-only as tests passed. automation_verified is true only after authorized execute."""
        return json.dumps(
            run_verification(
                _db_path(),
                execute=execute,
                target=target or None,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("list_capabilities")
    def _capabilities() -> str:
        """List CLI/MCP capabilities and verify authorization requirements."""
        return json.dumps(list_capabilities(), ensure_ascii=False, indent=2)

    @_experimental("render_studio")
    def _studio(out: str = "", target: str = "", lang: str = "en") -> str:
        """Render Studio HTML (status/graph/evidence/report); optional out/target/lang."""
        return json.dumps(
            render_studio(
                _db_path(),
                out=Path(out) if out else None,
                target=target or None,
                lang=lang or "en",
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("refresh_evidence")
    def _refresh_evidence() -> str:
        """Mark persisted evidence stale when watched file hashes changed."""
        return json.dumps(refresh_evidence(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("ingest_runtime_traces")
    def _ingest_traces(trace_path: str) -> str:
        """Ingest optional JSONL runtime call traces into relations + evidence."""
        return json.dumps(
            ingest_runtime_traces(_db_path(), Path(trace_path)),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("query_lsp")
    def _query_lsp(name: str, limit: int = 20) -> str:
        """Optional Jedi LSP definitions/references for a symbol name."""
        return json.dumps(
            query_lsp(_db_path(), name, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("repo_overview")
    def _overview() -> str:
        """Get repository index overview with an evidence envelope."""
        return json.dumps(repo_overview(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("repo_status")
    def _status() -> str:
        """Aggregate overview, health, snapshots, and recent verification state."""
        return json.dumps(repo_status(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("list_commits")
    def _commits(limit: int = 20) -> str:
        """List commits persisted from explain_change."""
        return json.dumps(
            list_commits(_db_path(), limit=limit), ensure_ascii=False, indent=2
        )

    @_experimental("list_index_snapshots")
    def _snapshots(limit: int = 20) -> str:
        """List index snapshots recorded after each index run."""
        return json.dumps(
            list_index_snapshots(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("refresh_index")
    def _refresh() -> str:
        """Incrementally re-index the repository stored in the DB."""
        return json.dumps(refresh_index(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("export_relation_graph")
    def _graph(target: str, format: str = "mermaid", limit: int = 40) -> str:
        """Export a neighborhood relation graph as Mermaid or DOT."""
        return json.dumps(
            export_relation_graph(
                _db_path(), target, limit=limit, fmt=format
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("list_test_results")
    def _test_results(limit: int = 50) -> str:
        """List persisted verification step/test results."""
        return json.dumps(
            list_test_results(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("repo_search")
    def _search(query: str, limit: int = 50) -> str:
        """Search indexed symbols/paths; returns evidence-graded matches."""
        return json.dumps(
            repo_search(_db_path(), query=query, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("trace_symbol")
    def _trace(name: str, limit: int = 50) -> str:
        """Locate symbol definitions (call/reference graph expands later)."""
        return json.dumps(
            trace_symbol(_db_path(), name=name, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("explain_code")
    def _explain_code(name: str, limit: int = 20, revision: str = "") -> str:
        """Explain a symbol with snippet, blame, and caller evidence."""
        return json.dumps(
            explain_code(
                _db_path(),
                name=name,
                limit=limit,
                revision=revision or None,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("explain_change")
    def _explain(revision: str = "HEAD", limit: int = 50) -> str:
        """Explain a git revision with file changes and indexed symbols."""
        return json.dumps(
            explain_change(_db_path(), revision=revision, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("analyze_impact")
    def _impact(target: str, limit: int = 50) -> str:
        """Estimate blast radius for a symbol via calls/imports."""
        return json.dumps(
            analyze_impact(_db_path(), target=target, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("analyze_change_impact")
    def _change_impact(revision: str = "HEAD", limit: int = 50) -> str:
        """Blast radius for symbols overlapping unified-diff hunks in a revision."""
        return json.dumps(
            analyze_change_impact(_db_path(), revision=revision, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("analyze_pr_impact")
    def _pr_impact(base_ref: str, head_ref: str = "HEAD", limit: int = 50) -> str:
        """PR-range (three-dot) blast radius + evidence; prefer over single-commit change-impact."""
        from witnis.core.pr_gate import analyze_pr_impact

        return json.dumps(
            analyze_pr_impact(
                _db_path(), base_ref=base_ref, head_ref=head_ref, limit=limit
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("run_pr_gate")
    def _pr_gate(
        base_ref: str,
        head_ref: str = "HEAD",
        with_plan: bool = True,
        execute_verify: bool = False,
        strict: bool = False,
    ) -> str:
        """Build PR evidence gate payload (markdown inside JSON). Verify stays gated."""
        from witnis.core.pr_gate import run_pr_gate

        db = _db_path()
        root = Path(db).resolve().parent.parent
        return json.dumps(
            run_pr_gate(
                db,
                base_ref=base_ref,
                head_ref=head_ref,
                root=root if root.exists() else Path.cwd(),
                reindex=True,
                with_plan=with_plan,
                execute_verify=execute_verify,
                strict=strict,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("check_import_graph")
    def _import_graph(limit: int = 100) -> str:
        """Check indexed local import edges for broken targets."""
        return json.dumps(
            check_import_graph(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("check_index_health")
    def _doctor() -> str:
        """Structural health check for the local Witnis index."""
        return json.dumps(check_index_health(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("check_python_syntax")
    def _syntax() -> str:
        """AST-parse indexed Python files for syntax errors."""
        return json.dumps(check_python_syntax(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("compare_revisions")
    def _compare(base: str, head: str = "HEAD", limit: int = 100) -> str:
        """Compare Python/JS/TS/Java symbol deltas between two git revisions."""
        return json.dumps(
            compare_revisions(_db_path(), base=base, head=head, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("compare_worktree")
    def _compare_worktree(limit: int = 100) -> str:
        """Compare dirty worktree against HEAD for symbol deltas."""
        return json.dumps(
            compare_worktree(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("scan_secrets")
    def _scan_secrets(limit: int = 50) -> str:
        """Heuristic secret-like assignment scan with redacted previews."""
        return json.dumps(
            scan_secrets(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("find_related_tests")
    def _tests(target: str, limit: int = 50) -> str:
        """Heuristically find related tests for a symbol."""
        return json.dumps(
            find_related_tests(_db_path(), target=target, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("get_evidence")
    def _evidence(query: str, limit: int = 50, status: str = "") -> str:
        """Collect symbol/relation evidence for a query; optional status filter."""
        return json.dumps(
            get_evidence(
                _db_path(),
                query=query,
                limit=limit,
                status=status or None,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("export_evidence_bundle")
    def _export_bundle(
        target: str = "", revision: str = "", limit: int = 50
    ) -> str:
        """Pack overview/trace/impact/tests/change into one evidence bundle."""
        return json.dumps(
            export_evidence_bundle(
                _db_path(),
                target=target or None,
                revision=revision or None,
                limit=limit,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("render_evidence_report")
    def _report(target: str = "", revision: str = "", limit: int = 50) -> str:
        """Render a Markdown evidence report for agents/humans."""
        return json.dumps(
            render_evidence_report(
                _db_path(),
                target=target or None,
                revision=revision or None,
                limit=limit,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("create_verification_plan")
    def _plan(target: str = "", revision: str = "") -> str:
        """Create a read-only verification plan (no execution)."""
        return json.dumps(
            create_verification_plan(
                _db_path(),
                target=target or None,
                revision=revision or None,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("run_verification")
    def _run(target: str = "", revision: str = "", execute: bool = False) -> str:
        """Preview or execute verification. execute requires WITNIS_ALLOW_VERIFY=1."""
        return json.dumps(
            run_verification(
                _db_path(),
                execute=execute,
                target=target or None,
                revision=revision or None,
            ),
            ensure_ascii=False,
            indent=2,
        )

    @_experimental("get_verification_report")
    def _report() -> str:
        """Return the last verification plan/report."""
        return json.dumps(get_verification_report(_db_path()), ensure_ascii=False, indent=2)

    @_experimental("list_verification_runs")
    def _runs(limit: int = 20) -> str:
        """List persisted verification runs (newest first)."""
        return json.dumps(
            list_verification_runs(_db_path(), limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    return server


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
