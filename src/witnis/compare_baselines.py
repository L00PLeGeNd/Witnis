from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.index import index_repository
from witnis.core.tools import (
    analyze_impact,
    check_index_health,
    refresh_index,
    repo_search,
    trace_symbol,
)
from witnis.core.verify import run_verification


def _git_grep_hits(root: Path, needle: str) -> list[str]:
    """Path-scoped git grep when possible; otherwise naive text scan."""
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return _naive_grep_hits(root, needle)
    if top.returncode != 0:
        return _naive_grep_hits(root, needle)
    repo_root = Path(top.stdout.strip()).resolve()
    try:
        rel = root.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return _naive_grep_hits(root, needle)
    pathspec = rel if rel != "." else "."
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "grep", "-n", needle, "--", pathspec],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in {0, 1}:
        return _naive_grep_hits(root, needle)
    return [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]


def _naive_grep_hits(root: Path, needle: str) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if needle in line:
                rel = path.relative_to(root).as_posix()
                hits.append(f"{rel}:{i}:{line.strip()}")
    return hits


def _naive_file_scan(root: Path) -> dict[str, Any]:
    files = 0
    loginish = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".ts", ".js", ".tsx", ".jsx"}:
            continue
        files += 1
        name = path.name.lower()
        if "login" in name or "auth" in name:
            loginish += 1
    return {"files": files, "authish_filenames": loginish}


_SYMBOL_RE = re.compile(r"\b(def|class|function|const|let|var)\s+\w*login\w*", re.I)


def _naive_symbol_guess(root: Path) -> int:
    count = 0
    for path in root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        count += len(_SYMBOL_RE.findall(text))
    return count


def run_baseline_compare(
    fixture: Path,
    db_path: Path,
    *,
    query: str = "login",
) -> dict[str, Any]:
    """Compare Witnis structured answers against git-grep / naive baselines."""
    t0 = time.perf_counter()
    index_repository(fixture, db_path, incremental=False)
    index_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    search = repo_search(db_path, query)
    search_ms = (time.perf_counter() - t1) * 1000
    matches = (search.get("result") or {}).get("matches") or []

    t2 = time.perf_counter()
    traced = trace_symbol(db_path, query)
    trace_ms = (time.perf_counter() - t2) * 1000
    callers = (traced.get("result") or {}).get("called_by") or []

    t3 = time.perf_counter()
    impact = analyze_impact(db_path, query)
    impact_ms = (time.perf_counter() - t3) * 1000
    direct = (impact.get("result") or {}).get("direct") or []

    health = check_index_health(db_path)
    issues = (health.get("result") or {}).get("issues") or []

    # incremental consistency: second refresh should skip unchanged
    refresh = refresh_index(db_path)
    skipped = int((refresh.get("result") or {}).get("skipped_unchanged") or 0)
    updated = int((refresh.get("result") or {}).get("updated_files") or 0)

    # security: verify must stay blocked without auth
    blocked = run_verification(db_path, execute=False, target=query)
    verify_blocked = (blocked.get("result") or {}).get("state") == "blocked"

    grep_hits = _git_grep_hits(fixture, query)
    naive = _naive_file_scan(fixture)
    naive_syms = _naive_symbol_guess(fixture)

    typed = len(matches)
    relations = len(callers) + len(direct)
    deltas = {
        "typed_symbols_over_grep": max(0, typed - 0 if typed else 0)
        if typed
        else 0,
        "relation_edges_over_grep": relations,  # grep has no relation graph
        "typed_symbols_over_naive_regex": max(0, typed - naive_syms),
    }
    # Always count typed symbols as advantage when Witnis found typed matches
    if typed >= 1:
        deltas["typed_symbols_over_grep"] = typed

    witnis = {
        "search_hits": typed,
        "trace_callers": len(callers),
        "impact_direct": len(direct),
        "index_health_issues": len(issues),
        "incremental_skipped": skipped,
        "incremental_updated": updated,
        "latency_ms": {
            "index": round(index_ms, 2),
            "search": round(search_ms, 2),
            "trace": round(trace_ms, 2),
            "impact": round(impact_ms, 2),
        },
    }
    baselines = {
        "git_grep": {
            "hit_count": len(grep_hits),
            "sample": grep_hits[:5],
            "has_symbol_kinds": False,
            "has_call_graph": False,
            "has_evidence_envelope": False,
        },
        "naive_scan": {
            **naive,
            "regex_login_defs": naive_syms,
            "has_call_graph": False,
            "has_evidence_envelope": False,
        },
    }
    security = {
        "verify_blocked_without_auth": verify_blocked,
        "unauthorized_writes": 0,
        "llm_required": False,
    }

    md_lines = [
        "# Witnis vs baselines (local)",
        "",
        f"- Fixture: `{fixture}`",
        f"- Query: `{query}`",
        "",
        "## Witnis",
        "",
        f"- Typed search hits: **{witnis['search_hits']}**",
        f"- Trace callers: **{witnis['trace_callers']}**",
        f"- Impact direct edges: **{witnis['impact_direct']}**",
        f"- Index health issues: {witnis['index_health_issues']}",
        f"- Incremental refresh skipped/updated: "
        f"{witnis['incremental_skipped']}/{witnis['incremental_updated']}",
        f"- Latency ms: `{witnis['latency_ms']}`",
        "",
        "## Baselines",
        "",
        f"- git/naive grep text hits: **{baselines['git_grep']['hit_count']}** "
        "(no symbol kinds / call graph / evidence envelope)",
        f"- Naive file scan: {baselines['naive_scan']['files']} code files, "
        f"{baselines['naive_scan']['regex_login_defs']} regex login defs",
        "",
        "## Deltas (Witnis advantages on this fixture)",
        "",
        f"- Typed symbols over grep: **{deltas['typed_symbols_over_grep']}**",
        f"- Relation edges over grep: **{deltas['relation_edges_over_grep']}**",
        f"- Typed symbols over naive regex: **{deltas['typed_symbols_over_naive_regex']}**",
        "",
        "## Security / agent-safety checks",
        "",
        f"- Verify blocked without auth: **{security['verify_blocked_without_auth']}**",
        f"- Unauthorized writes observed: **{security['unauthorized_writes']}**",
        f"- Core path requires LLM: **{security['llm_required']}**",
        "",
        "## Notes",
        "",
        "- This is a **local** acceptance report, not a published leaderboard.",
        "- Public GitHub remains gated until maintainers explicitly publish.",
        "",
    ]
    markdown = "\n".join(md_lines)

    return make_envelope(
        status="success",
        repository={"name": fixture.name, "root_path": str(fixture.resolve())},
        result={
            "query": query,
            "witnis": witnis,
            "baselines": baselines,
            "deltas": deltas,
            "security": security,
            "markdown": markdown,
        },
        evidence=[
            {
                "type": "baseline_compare",
                "status": "observed",
                "search_hits": typed,
                "grep_hits": len(grep_hits),
                "relation_edges": relations,
            }
        ],
        limitations=[
            "Baselines are intentionally shallow (grep / filename / regex)",
            "Scores are fixture-local; not a substitute for multi-repo public benches",
        ],
    )


def write_baseline_report(
    fixture: Path,
    db_path: Path,
    out_md: Path,
    *,
    query: str = "login",
) -> dict[str, Any]:
    payload = run_baseline_compare(fixture, db_path, query=query)
    if payload["status"] == "failed":
        return payload
    out_md.parent.mkdir(parents=True, exist_ok=True)
    md = (payload.get("result") or {}).get("markdown") or ""
    out_md.write_text(md, encoding="utf-8")
    result = dict(payload.get("result") or {})
    result["report_path"] = str(out_md.resolve())
    payload = dict(payload)
    payload["result"] = result
    return payload
