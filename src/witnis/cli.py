from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from witnis.bench import run_benchmark
from witnis.core.index import index_repository
from witnis import __version__
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
    refresh_index,
    render_evidence_report,
    repo_overview,
    repo_search,
    repo_status,
    ingest_runtime_traces,
    query_lsp,
    refresh_evidence,
    scan_secrets,
    trace_symbol,
)
from witnis.compare_baselines import write_baseline_report
from witnis.studio import render_studio
import time
import webbrowser
from witnis.core.verify import (
    create_verification_plan,
    get_verification_report,
    list_verification_runs,
    run_verification,
)

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Witnis CLI")


def _default_db() -> Path:
    return Path.cwd() / ".witnis" / "index.sqlite"


@app.command("version")
def version_cmd() -> None:
    """Print Witnis version."""
    typer.echo(__version__)


@app.command("capabilities")
def capabilities_cmd() -> None:
    """List CLI commands and MCP tools for agents."""
    typer.echo(json.dumps(list_capabilities(), ensure_ascii=False, indent=2))


@app.command("studio")
def studio_cmd(
    out: Optional[Path] = typer.Option(None, "--out", help="HTML output path"),
    target: Optional[str] = typer.Option(
        None, "--target", help="Symbol focus for graph/evidence/report panels"
    ),
    lang: str = typer.Option("en", "--lang", help="UI language: en|zh|pt|fr|ru"),
    open_browser: bool = typer.Option(
        False, "--open", help="Open the rendered dashboard in a browser"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Render Studio HTML dashboard (status, graph, evidence, report)."""
    db_path = db or _default_db()
    try:
        payload = render_studio(db_path, out=out, target=target, lang=lang)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    path = (payload.get("result") or {}).get("path")
    if open_browser and path:
        webbrowser.open(Path(path).resolve().as_uri())
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("refresh-evidence")
def refresh_evidence_cmd(
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Mark persisted evidence stale when watched file hashes changed."""
    db_path = db or _default_db()
    try:
        payload = refresh_evidence(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("ingest-traces")
def ingest_traces_cmd(
    trace: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Ingest optional JSONL runtime call traces into relations + evidence."""
    db_path = db or _default_db()
    try:
        payload = ingest_runtime_traces(db_path, trace)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("lsp")
def lsp_cmd(
    name: str = typer.Argument(..., help="Symbol name"),
    db: Optional[Path] = typer.Option(None, "--db"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """Optional Jedi LSP definitions/references (requires witnis[lsp])."""
    db_path = db or _default_db()
    try:
        payload = query_lsp(db_path, name, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("compare-baselines")
def compare_baselines_cmd(
    path: Path = typer.Argument(
        ..., exists=True, file_okay=False, dir_okay=True, help="Fixture/repo root"
    ),
    query: str = typer.Option("login", "--query"),
    out: Optional[Path] = typer.Option(
        None, "--out", help="Markdown report path (default: docs/benchmarks/local-v1.md)"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Compare Witnis against git-grep / naive baselines (local acceptance)."""
    db_path = db or (Path.cwd() / ".witnis" / "baseline.sqlite")
    report_path = out or (Path.cwd() / "docs" / "benchmarks" / "local-v1.md")
    try:
        payload = write_baseline_report(path, db_path, report_path, query=query)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("watch")
def watch_cmd(
    interval: int = typer.Option(20, "--interval", help="Seconds between refreshes"),
    cycles: int = typer.Option(0, "--cycles", help="Stop after N cycles (0=forever)"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Periodically incremental-refresh the index (Ctrl+C to stop)."""
    db_path = db or _default_db()
    n = 0
    while True:
        n += 1
        try:
            payload = refresh_index(db_path)
        except FileNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        result = payload.get("result") or {}
        typer.echo(
            f"[{n}] updated={result.get('updated_files')} "
            f"skipped={result.get('skipped_unchanged')} "
            f"removed={result.get('removed_files')}"
        )
        if cycles and n >= cycles:
            break
        time.sleep(max(1, interval))


@app.command("index")
def index_cmd(
    path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    full: bool = typer.Option(
        False, "--full", help="Force full rebuild instead of incremental"
    ),
) -> None:
    """Index a repository into the local SQLite store."""
    db_path = db or _default_db()
    stats = index_repository(path, db_path, incremental=not full)
    typer.echo(
        f"indexed repo={stats.repository} files={stats.files} "
        f"symbols={stats.symbols} updated={stats.updated_files} "
        f"skipped={stats.skipped_unchanged} removed={stats.removed_files} "
        f"db={stats.db_path}"
    )


@app.command("overview")
def overview_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    as_json: bool = typer.Option(False, "--json", help="Evidence envelope JSON"),
) -> None:
    """Show index overview for the latest repository."""
    db_path = db or _default_db()
    try:
        payload = repo_overview(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        if payload["status"] == "failed":
            raise typer.Exit(code=1)
        return
    if payload["status"] == "failed":
        typer.echo("empty index")
        raise typer.Exit(code=1)
    repo = payload["repository"]
    result = payload["result"]
    typer.echo(
        f"repository={repo['name']} root={repo['root_path']} "
        f"files={result['files']} symbols={result['symbols']}"
    )


@app.command("status")
def status_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Aggregate overview, health, snapshots, and recent verification state."""
    db_path = db or _default_db()
    try:
        payload = repo_status(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("commits")
def commits_cmd(
    limit: int = typer.Option(20, "--limit"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """List commits persisted from explain-change."""
    db_path = db or _default_db()
    try:
        payload = list_commits(db_path, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("snapshots")
def snapshots_cmd(
    limit: int = typer.Option(20, "--limit"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """List index snapshots recorded after each index run."""
    db_path = db or _default_db()
    try:
        payload = list_index_snapshots(db_path, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("refresh")
def refresh_cmd(
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Incrementally re-index the repository already stored in the DB."""
    db_path = db or _default_db()
    try:
        payload = refresh_index(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("graph")
def graph_cmd(
    target: str = typer.Argument(..., help="Symbol focus"),
    fmt: str = typer.Option("mermaid", "--format", help="mermaid|dot"),
    out: Optional[Path] = typer.Option(None, "--out"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Export a neighborhood relation graph (Mermaid or DOT)."""
    db_path = db or _default_db()
    try:
        payload = export_relation_graph(db_path, target, fmt=fmt)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    text = (payload.get("result") or {}).get("graph") or ""
    if out:
        out.write_text(text, encoding="utf-8")
        typer.echo(str(out))
    else:
        typer.echo(text if text else json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("test-results")
def test_results_cmd(
    limit: int = typer.Option(50, "--limit"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """List persisted verification step/test results."""
    db_path = db or _default_db()
    try:
        payload = list_test_results(db_path, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("search")
def search_cmd(
    query: str = typer.Argument(...),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    limit: int = typer.Option(50, "--limit"),
    as_json: bool = typer.Option(False, "--json", help="Evidence envelope JSON"),
) -> None:
    """Search indexed symbols and paths."""
    db_path = db or _default_db()
    try:
        payload = repo_search(db_path, query=query, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        if not payload["result"]["matches"]:
            raise typer.Exit(code=1)
        return
    hits = payload["result"]["matches"]
    if not hits:
        typer.echo("no matches")
        raise typer.Exit(code=1)
    for hit in hits:
        typer.echo(
            f"{hit['kind']}\t{hit['name']}\t{hit['file_path']}:"
            f"{hit['start_line']}-{hit['end_line']}"
        )


@app.command("explain")
def explain_cmd(
    name: str = typer.Argument(..., help="Symbol name"),
    revision: Optional[str] = typer.Option(
        None, "--revision", help="Read snippet from git blob at revision"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Explain a symbol with snippet, blame, and callers."""
    db_path = db or _default_db()
    try:
        payload = explain_code(db_path, name=name, revision=revision)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("trace")
def trace_cmd(
    name: str = typer.Argument(..., help="Symbol name"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    as_json: bool = typer.Option(True, "--json/--plain", help="Evidence envelope JSON"),
) -> None:
    """Trace a symbol definition (call graph expands later)."""
    db_path = db or _default_db()
    try:
        payload = trace_symbol(db_path, name=name)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for hit in payload["result"]["definitions"]:
            typer.echo(
                f"{hit['kind']}\t{hit['name']}\t{hit['file_path']}:"
                f"{hit['start_line']}-{hit['end_line']}"
            )
    if not payload["result"]["definitions"]:
        raise typer.Exit(code=1)


@app.command("impact")
def impact_cmd(
    target: str = typer.Argument(..., help="Symbol or module name"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    as_json: bool = typer.Option(True, "--json/--plain", help="Evidence envelope JSON"),
) -> None:
    """Estimate blast radius for a symbol using indexed relations."""
    db_path = db or _default_db()
    try:
        payload = analyze_impact(db_path, target=target)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for edge in payload["result"].get("direct", []):
            typer.echo(
                f"Direct\t{edge.get('relation_type')}\t"
                f"{edge.get('source')} -> {edge.get('target')}"
            )
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("change-impact")
def change_impact_cmd(
    revision: str = typer.Argument("HEAD", help="Git revision"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Estimate blast radius for symbols overlapping diff hunks in a revision."""
    db_path = db or _default_db()
    try:
        payload = analyze_change_impact(db_path, revision=revision)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("import-graph")
def import_graph_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Check indexed import edges against known local modules."""
    db_path = db or _default_db()
    try:
        payload = check_import_graph(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("doctor")
def doctor_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Run structural health checks on the local index."""
    db_path = db or _default_db()
    try:
        payload = check_index_health(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] != "success":
        raise typer.Exit(code=1)


@app.command("syntax")
def syntax_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """AST-parse indexed Python files for syntax errors."""
    db_path = db or _default_db()
    try:
        payload = check_python_syntax(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload.get("result", {}).get("errors"):
        raise typer.Exit(code=1)


@app.command("compare")
def compare_cmd(
    base: str = typer.Argument(..., help="Base git revision"),
    head: str = typer.Argument("HEAD", help="Head git revision"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Compare Python/JS/TS symbol deltas between two revisions."""
    db_path = db or _default_db()
    try:
        payload = compare_revisions(db_path, base=base, head=head)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("compare-worktree")
def compare_worktree_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Compare dirty worktree (+untracked) against HEAD for symbol deltas."""
    db_path = db or _default_db()
    try:
        payload = compare_worktree(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("scan-secrets")
def scan_secrets_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Heuristic secret-like assignment scan with redacted previews."""
    db_path = db or _default_db()
    try:
        payload = scan_secrets(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload.get("result", {}).get("finding_count", 0) > 0:
        raise typer.Exit(code=1)


@app.command("export-bundle")
def export_bundle_cmd(
    target: Optional[str] = typer.Option(None, "--target", help="Symbol focus"),
    revision: Optional[str] = typer.Option(None, "--revision", help="Git revision"),
    out: Optional[Path] = typer.Option(None, "--out", help="Write JSON to path"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Export an agent-facing evidence bundle for a target and/or revision."""
    db_path = db or _default_db()
    try:
        payload = export_evidence_bundle(
            db_path, target=target, revision=revision
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out:
        out.write_text(text, encoding="utf-8")
        typer.echo(str(out))
    else:
        typer.echo(text)
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    target: Optional[str] = typer.Option(None, "--target", help="Symbol focus"),
    revision: Optional[str] = typer.Option(None, "--revision", help="Git revision"),
    out: Optional[Path] = typer.Option(None, "--out", help="Write Markdown to path"),
    html_out: Optional[Path] = typer.Option(
        None, "--html-out", help="Write HTML preview to path"
    ),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Render a Markdown/HTML evidence report (Studio-lite)."""
    db_path = db or _default_db()
    try:
        payload = render_evidence_report(
            db_path, target=target, revision=revision
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    md = (payload.get("result") or {}).get("markdown") or ""
    html = (payload.get("result") or {}).get("html") or ""
    if html_out:
        html_out.write_text(html, encoding="utf-8")
        typer.echo(str(html_out))
    if out:
        out.write_text(md, encoding="utf-8")
        typer.echo(str(out))
    if not out and not html_out:
        typer.echo(md)
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("related-tests")
def related_tests_cmd(
    target: str = typer.Argument(..., help="Symbol name"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """List heuristically related tests for a symbol."""
    db_path = db or _default_db()
    try:
        payload = find_related_tests(db_path, target=target)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("explain-change")
def explain_change_cmd(
    revision: str = typer.Argument("HEAD", help="Git revision to explain"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    as_json: bool = typer.Option(True, "--json/--plain", help="Evidence envelope JSON"),
) -> None:
    """Explain a git commit using observed diff metadata + indexed symbols."""
    db_path = db or _default_db()
    try:
        payload = explain_change(db_path, revision=revision)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        commit = payload["result"].get("commit") or {}
        typer.echo(f"{commit.get('hash', '?')} {commit.get('subject', '')}")
        for change in payload["result"].get("files", []):
            typer.echo(f"{change.get('status')}\t{change.get('path')}")
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("evidence")
def evidence_cmd(
    query: str = typer.Argument(..., help="Symbol or path query"),
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter persisted evidence by status (e.g. verified)"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Dump evidence envelope for a query."""
    db_path = db or _default_db()
    try:
        payload = get_evidence(db_path, query=query, status=status)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload.get("evidence"):
        raise typer.Exit(code=1)


@app.command("plan-verify")
def plan_verify_cmd(
    target: Optional[str] = typer.Option(None, "--target", help="Symbol to focus"),
    revision: Optional[str] = typer.Option(None, "--revision", help="Git revision"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Create a read-only verification plan (no command execution)."""
    db_path = db or _default_db()
    try:
        payload = create_verification_plan(
            db_path, target=target, revision=revision
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("verify")
def verify_cmd(
    target: Optional[str] = typer.Option(None, "--target"),
    revision: Optional[str] = typer.Option(None, "--revision"),
    execute: bool = typer.Option(
        False, "--execute", help="Execute pytest steps (also needs WITNIS_ALLOW_VERIFY=1)"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Run or preview verification. Defaults to blocked without --execute."""
    db_path = db or _default_db()
    try:
        payload = run_verification(
            db_path, execute=execute, target=target, revision=revision
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["result"].get("state") == "failed":
        raise typer.Exit(code=1)


@app.command("verification-report")
def verification_report_cmd(
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Show the last verification plan/report."""
    db_path = db or _default_db()
    try:
        payload = get_verification_report(db_path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("verification-history")
def verification_history_cmd(
    limit: int = typer.Option(20, "--limit"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """List persisted verification runs (newest first)."""
    db_path = db or _default_db()
    try:
        payload = list_verification_runs(db_path, limit=limit)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("bench")
def bench_cmd(
    suite: str = typer.Option(
        "local",
        "--suite",
        help="Benchmark suite: local | public",
    ),
    tasks: Optional[Path] = typer.Option(
        None,
        "--tasks",
        exists=True,
        dir_okay=False,
        help="Override benchmark task file",
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Run reproducible benchmark tasks (local fixture or public suite)."""
    db_path = db or (_default_db().parent / "bench.sqlite")
    repo_root = Path.cwd()
    if tasks is None:
        tasks = (
            Path("benchmarks/public/tasks.json")
            if suite == "public"
            else Path("benchmarks/tasks.json")
        )
    if not tasks.exists():
        typer.echo(f"missing tasks file: {tasks}", err=True)
        raise typer.Exit(code=1)
    report = run_benchmark(repo_root, tasks, db_path)
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    if report["passed"] < report["total"]:
        raise typer.Exit(code=1)


@app.command("mcp")
def mcp_cmd(
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Run read-only Witnis MCP server on stdio."""
    import os

    from witnis.mcp_server import build_server

    db_path = db or _default_db()
    os.environ["WITNIS_DB"] = str(db_path.resolve())
    build_server().run(transport="stdio")


if __name__ == "__main__":
    app()
