from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from witnis.bench import run_benchmark
from witnis.core.index import index_repository
from witnis import __version__
from witnis.core.loop_init import init_trusted_loop
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

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Witnis — witness claims with evidence",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _default_db() -> Path:
    return Path.cwd() / ".witnis" / "index.sqlite"


def _focus(*parts: Optional[str]) -> Optional[str]:
    for part in parts:
        if part:
            return part
    return None


def _print_json(payload: dict) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("version")
def version_cmd() -> None:
    """Print Witnis version."""
    typer.echo(__version__)


@app.command("capabilities")
def capabilities_cmd() -> None:
    """List CLI commands and MCP tools for agents."""
    typer.echo(json.dumps(list_capabilities(), ensure_ascii=False, indent=2))


@app.command("loop-init")
def loop_init_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Repo root (default: cwd)"
    ),
    no_harnis: bool = typer.Option(
        False,
        "--no-harnis",
        help="Write Witnis-only MCP config (skip Harnis seatbelt wrap)",
    ),
    deny_verify: bool = typer.Option(
        False,
        "--deny-verify",
        help="Harnis policy denies run_verification until you edit it",
    ),
    python_harnis: bool = typer.Option(
        False,
        "--python-harnis",
        help="Wrap with python -m harnis instead of npx -y harnis",
    ),
    no_index: bool = typer.Option(
        False, "--no-index", help="Skip indexing after writing configs"
    ),
) -> None:
    """Bootstrap Trusted Agent Loop: MCP config + optional Harnis wrap + index."""
    root = (path or Path.cwd()).resolve()
    if not root.is_dir():
        typer.echo(f"Not a directory: {root}", err=True)
        raise typer.Exit(code=1)
    try:
        payload = init_trusted_loop(
            root,
            with_harnis=not no_harnis,
            deny_verify=deny_verify,
            use_npx=not python_harnis,
            index=not no_index,
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("studio")
def studio_cmd(
    name: Optional[str] = typer.Argument(None, help="Symbol to focus"),
    out: Optional[Path] = typer.Option(None, "--out", help="HTML output path"),
    target: Optional[str] = typer.Option(
        None, "--target", help="Symbol focus (alias of positional name)"
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
        payload = render_studio(
            db_path, out=out, target=_focus(name, target), lang=lang
        )
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


@app.command("baselines")
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
    """Compare Witnis vs grep/regex baselines (alias: baselines)."""
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


@app.command("look")
def look_cmd(
    name: str = typer.Argument(..., help="Symbol to inspect"),
    db: Optional[Path] = typer.Option(None, "--db"),
    as_json: bool = typer.Option(False, "--json", help="Full envelopes as JSON"),
) -> None:
    """One-shot witness card: search + trace + impact + related tests."""
    db_path = db or _default_db()
    try:
        search = repo_search(db_path, query=name, limit=8)
        trace = trace_symbol(db_path, name=name)
        impact = analyze_impact(db_path, target=name)
        tests = find_related_tests(db_path, target=name)
        plan = create_verification_plan(db_path, target=name)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if as_json:
        _print_json(
            {
                "status": "success",
                "result": {
                    "search": search.get("result"),
                    "trace": trace.get("result"),
                    "impact": impact.get("result"),
                    "tests": tests.get("result"),
                    "plan": plan.get("result"),
                },
            }
        )
        return

    matches = (search.get("result") or {}).get("matches") or []
    defs = (trace.get("result") or {}).get("definitions") or []
    called_by = (trace.get("result") or {}).get("called_by") or []
    direct = (impact.get("result") or {}).get("direct") or []
    related = (tests.get("result") or {}).get("tests") or []
    steps = (plan.get("result") or {}).get("steps") or []

    typer.echo(name)
    if matches:
        m = matches[0]
        typer.echo(
            f"  hit     {m.get('kind')}  {m.get('name')}  "
            f"{m.get('file_path')}:{m.get('start_line')}"
        )
    for d in defs[:3]:
        typer.echo(
            f"  def     {d.get('kind')}  {d.get('name')}  "
            f"{d.get('file_path')}:{d.get('start_line')}"
        )
    for edge in called_by[:4]:
        typer.echo(f"  caller  {edge.get('source')}")
    typer.echo(f"  impact  {len(direct)} direct edge(s)")
    if related:
        paths = ", ".join(sorted({str(t.get('file_path')) for t in related[:5]}))
        typer.echo(f"  tests   {paths}")
    else:
        typer.echo("  tests   (none indexed)")
    typer.echo(f"  plan    {len(steps)} step(s) — run: witnis verify {name} --execute")


@app.command("up")
def up_cmd(
    root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Repo root to index",
    ),
    symbol: str = typer.Option("login", "--symbol", "-s", help="Symbol for look card"),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Index a repo, then print a look card (index + look)."""
    db_path = db or _default_db()
    typer.echo(f"index  {root.resolve()}")
    stats = index_repository(root, db_path, incremental=True)
    typer.echo(f"ready  {stats.files} files · {stats.symbols} symbols")
    look_cmd(name=symbol, db=db_path, as_json=False)


@app.command("demo")
def demo_cmd(
    root: Path = typer.Argument(
        Path("fixtures/mini_py"),
        exists=False,
        help="Repo/fixture to index (default: fixtures/mini_py)",
    ),
    symbol: str = typer.Option("login", "--symbol", "-s"),
    open_studio: bool = typer.Option(False, "--studio", help="Also render Studio HTML"),
) -> None:
    """Index a sample tree and print a look card (fast first run)."""
    db_path = Path.cwd() / ".witnis" / "demo.sqlite"
    target = root if root.exists() else Path(__file__).resolve().parents[2] / root
    if not target.exists():
        typer.echo(f"not found: {root}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"index  {target}")
    stats = index_repository(target, db_path, incremental=False)
    typer.echo(f"ready  {stats.files} files · {stats.symbols} symbols")
    look_cmd(name=symbol, db=db_path, as_json=False)
    if open_studio:
        out = Path.cwd() / ".witnis" / "demo-studio.html"
        payload = render_studio(db_path, out=out, target=symbol, lang="en")
        path = (payload.get("result") or {}).get("path") or str(out)
        typer.echo(f"studio  {path}")
        webbrowser.open(Path(path).resolve().as_uri())


@app.command("scene")
def scene_cmd(
    as_json: bool = typer.Option(False, "--json", help="Machine-readable story card"),
    execute: bool = typer.Option(
        False, "--execute", help="Also run gated verify (needs WITNIS_ALLOW_VERIFY=1)"
    ),
    fixture: str = typer.Option(
        "fixtures/auth_refresh", "--fixture", help="Scene fixture path"
    ),
    symbol: str = typer.Option("refresh_token", "--symbol", "-s"),
) -> None:
    """Walk the auth-refresh demo as engineering results (not MCP tool names)."""
    from witnis.core.scene import format_scene_text, run_scene

    payload = run_scene(
        Path.cwd(),
        fixture_rel=fixture,
        symbol=symbol,
        execute_verify=execute,
    )
    if as_json:
        _print_json(payload)
        if payload.get("status") == "failed":
            raise typer.Exit(code=1)
        return
    typer.echo(format_scene_text(payload))
    if payload.get("status") == "failed":
        raise typer.Exit(code=1)


@app.command("experiment")
def experiment_cmd(
    pack: Path = typer.Option(
        Path("benchmarks/experiments/ab_analysis_pack.json"),
        "--pack",
        exists=True,
        dir_okay=False,
        help="A/B analysis pack JSON",
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", help="Write report JSON (default: benchmarks/experiments/reports/…)"
    ),
) -> None:
    """Reproduce grep vs Witnis analysis completeness (no LLM required)."""
    from witnis.core.ab_experiment import run_pack

    work = Path.cwd() / ".witnis" / "experiment"
    work.mkdir(parents=True, exist_ok=True)
    report = run_pack(Path.cwd(), pack, work)
    dest = out or (
        Path("benchmarks/experiments/reports")
        / f"{report.get('pack') or 'ab'}-latest.json"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    typer.echo(f"wrote  {dest}", err=True)


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


@app.command("pr-gate")
def pr_gate_cmd(
    base: str = typer.Option(..., "--base", help="PR base ref (e.g. origin/main)"),
    head: str = typer.Option("HEAD", "--head", help="PR head ref"),
    format: str = typer.Option(
        "markdown", "--format", help="markdown | json"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write body to file"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
    root: Optional[Path] = typer.Option(
        None, "--root", help="Repo root to (re)index; default cwd"
    ),
    no_reindex: bool = typer.Option(False, "--no-reindex", help="Skip index refresh"),
    with_plan: bool = typer.Option(
        True, "--with-plan/--no-plan", help="Include gated verify plan (blocked by default)"
    ),
    execute_verify: bool = typer.Option(
        False,
        "--execute-verify",
        help="Run verify (still needs WITNIS_ALLOW_VERIFY=1)",
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Non-zero exit on failed/uncertain/contradicted"
    ),
) -> None:
    """PR evidence gate: three-dot impact + markdown/JSON for CI comments."""
    from witnis.core.pr_gate import run_pr_gate

    db_path = db or _default_db()
    repo_root = (root or Path.cwd()).resolve()
    try:
        payload = run_pr_gate(
            db_path,
            base_ref=base,
            head_ref=head,
            root=repo_root,
            reindex=not no_reindex,
            with_plan=with_plan,
            execute_verify=execute_verify,
            strict=strict,
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    body = payload.get("markdown") if format == "markdown" else json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    if format == "json":
        # Keep markdown inside JSON payload; print full structure
        body = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        output.write_text(str(body), encoding="utf-8")
    else:
        typer.echo(body)
    raise typer.Exit(code=int(payload.get("exit_code") or 0))


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


@app.command("tests")
@app.command("related-tests")
def related_tests_cmd(
    target: str = typer.Argument(..., help="Symbol name"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """List related tests for a symbol (alias: tests)."""
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


@app.command("plan")
@app.command("plan-verify")
def plan_verify_cmd(
    name: Optional[str] = typer.Argument(None, help="Symbol to focus"),
    target: Optional[str] = typer.Option(None, "--target", help="Symbol to focus"),
    revision: Optional[str] = typer.Option(None, "--revision", help="Git revision"),
    db: Optional[Path] = typer.Option(None, "--db", help="SQLite index path"),
) -> None:
    """Create a read-only verification plan (alias: plan)."""
    db_path = db or _default_db()
    try:
        payload = create_verification_plan(
            db_path, target=_focus(name, target), revision=revision
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        raise typer.Exit(code=1)


@app.command("verify")
def verify_cmd(
    name: Optional[str] = typer.Argument(None, help="Symbol to focus"),
    target: Optional[str] = typer.Option(None, "--target"),
    revision: Optional[str] = typer.Option(None, "--revision"),
    execute: bool = typer.Option(
        False, "--execute", help="Run checks (also needs WITNIS_ALLOW_VERIFY=1)"
    ),
    db: Optional[Path] = typer.Option(None, "--db"),
) -> None:
    """Preview or run verification. Blocked without --execute."""
    db_path = db or _default_db()
    try:
        payload = run_verification(
            db_path,
            execute=execute,
            target=_focus(name, target),
            revision=revision,
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
        help="Benchmark suite: local | public | ground-truth",
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
    """Run reproducible benchmark tasks (local, public acceptance, or ground-truth)."""
    db_path = db or (_default_db().parent / "bench.sqlite")
    repo_root = Path.cwd()
    if suite in {"ground-truth", "gt"}:
        from witnis.core.ground_truth import run_ground_truth_suite

        work = db_path.parent / "gt-work"
        work.mkdir(parents=True, exist_ok=True)
        report = run_ground_truth_suite(
            labels_dir=repo_root / "benchmarks" / "ground-truth" / "labels",
            repo_root=repo_root,
            work_dir=work,
        )
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
        # Fail if any evaluated edge/symbol has false negatives
        if int(report.get("fn") or 0) > 0:
            raise typer.Exit(code=1)
        return
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
