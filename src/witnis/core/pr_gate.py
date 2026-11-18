"""PR evidence gate: merge-base range impact + markdown for GitHub comments."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.gitinfo import (
    git_commit_summary,
    git_diff_hunks_range,
    git_merge_base,
    git_name_status_triple_dot,
    git_show_blob,
)
from witnis.core.index import index_repository
from witnis.core.parse_js import parse_js_source
from witnis.core.parse_python import parse_python_source
from witnis.core.tools import (
    _JS_COMPARE_SUFFIXES,
    _dedupe_edges,
    _open_store,
    _repo_meta,
    _stale_bits,
    analyze_impact,
    compare_revisions,
)
from witnis.core.verify import create_verification_plan, run_verification

_IMPACT_SYMBOL_CAP = 20


def _hunk_overlaps(sym_start: int, sym_end: int, hunk: dict[str, Any]) -> bool:
    hs = int(hunk.get("start_line") or 0)
    he = int(hunk.get("end_line") or 0)
    if hs <= 0:
        return False
    return not (sym_end < hs or sym_start > he)


def _symbols_overlapping_hunks(
    root: Path, head: str, hunks: list[dict[str, Any]], *, limit: int
) -> list[dict[str, Any]]:
    by_path: dict[str, list[dict[str, Any]]] = {}
    for h in hunks:
        path = str(h.get("path") or "")
        if path:
            by_path.setdefault(path, []).append(h)

    out: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for path, path_hunks in by_path.items():
        suffix = Path(path).suffix.lower()
        blob = git_show_blob(root, head, path)
        if blob is None:
            continue
        if suffix == ".py":
            syms = parse_python_source(blob, rel_path=path)
        elif suffix in _JS_COMPARE_SUFFIXES:
            syms = parse_js_source(blob, rel_path=path)
        else:
            continue
        for sym in syms:
            if any(_hunk_overlaps(sym.start_line, sym.end_line, h) for h in path_hunks):
                key = (path, sym.name, sym.start_line)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file_path": path,
                        "start_line": sym.start_line,
                        "end_line": sym.end_line,
                        "source": "pr_hunk",
                    }
                )
                if len(out) >= limit:
                    return out
    return out


def analyze_pr_impact(
    db_path: Path,
    *,
    base_ref: str,
    head_ref: str = "HEAD",
    limit: int = 50,
    impact_symbol_cap: int = _IMPACT_SYMBOL_CAP,
) -> dict[str, Any]:
    """Blast radius for a GitHub-style PR range (base...head via merge-base)."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )

    root = Path(repo["root_path"])
    repository = _repo_meta(repo)
    stale_limits, stale_evidence = _stale_bits(repository)

    base_meta = git_commit_summary(root, base_ref)
    head_meta = git_commit_summary(root, head_ref)
    if base_meta is None or head_meta is None:
        return make_envelope(
            status="failed",
            repository=repository,
            result={},
            limitations=[f"Unable to resolve revisions: {base_ref!r} ... {head_ref!r}"],
            evidence=stale_evidence,
        )

    mb = git_merge_base(root, base_meta["hash"], head_meta["hash"])
    if not mb:
        return make_envelope(
            status="failed",
            repository=repository,
            result={"base": base_meta, "head": head_meta},
            limitations=["git merge-base failed for the given refs"],
            evidence=stale_evidence,
        )
    mb_meta = git_commit_summary(root, mb) or {"hash": mb}

    files = git_name_status_triple_dot(root, base_meta["hash"], head_meta["hash"])
    hunks = git_diff_hunks_range(
        root, base_meta["hash"], head_meta["hash"], triple_dot=True
    )
    compare = compare_revisions(
        db_path, base=mb, head=head_meta["hash"], limit=limit
    )
    symbols_in_hunks = _symbols_overlapping_hunks(
        root, head_meta["hash"], hunks, limit=limit
    )
    if not symbols_in_hunks:
        for row in (compare.get("result") or {}).get("symbols_added") or []:
            symbols_in_hunks.append({**row, "source": "pr_symbol_added"})
            if len(symbols_in_hunks) >= limit:
                break

    direct: list[dict[str, Any]] = []
    transitive: list[dict[str, Any]] = []
    related_tests: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = list(stale_evidence)
    evidence.append(
        {
            "type": "pr_range",
            "status": "observed",
            "base": base_meta["hash"],
            "head": head_meta["hash"],
            "merge_base": mb,
            "files": len(files),
            "hunks": len(hunks),
        }
    )
    limitations = list(stale_limits) + [
        "PR impact uses three-dot range (base...head) aligned with GitHub Files changed",
        "Impact edges are derived from the index — not runtime-proven",
    ]

    truncated = False
    for sym in symbols_in_hunks[:impact_symbol_cap]:
        name = str(sym.get("name") or "")
        if not name:
            continue
        impact = analyze_impact(db_path, name, limit=limit)
        direct.extend(impact.get("result", {}).get("direct") or [])
        transitive.extend(impact.get("result", {}).get("transitive") or [])
        related_tests.extend(impact.get("result", {}).get("related_tests") or [])
        evidence.extend(impact.get("evidence") or [])
    if len(symbols_in_hunks) > impact_symbol_cap:
        truncated = True
        limitations.append(
            f"Impact capped at {impact_symbol_cap} hunk symbols "
            f"(of {len(symbols_in_hunks)}); raise impact_symbol_cap if needed"
        )

    direct = _dedupe_edges(direct)[:limit]
    transitive = _dedupe_edges(transitive)[:limit]
    seen_t: set[tuple] = set()
    unique_tests: list[dict[str, Any]] = []
    for t in related_tests:
        key = (t.get("file_path"), t.get("name"))
        if key in seen_t:
            continue
        seen_t.add(key)
        unique_tests.append(t)

    status = "success" if files else "partial"
    if truncated and status == "success":
        status = "partial"

    return make_envelope(
        status=status,
        repository={
            **repository,
            "base": base_meta["hash"],
            "head": head_meta["hash"],
            "merge_base": mb,
        },
        result={
            "analysis_scope": "pr_range",
            "base": base_meta,
            "head": head_meta,
            "merge_base": mb_meta,
            "files": files[:limit],
            "file_count": len(files),
            "hunks": hunks[: limit * 2],
            "hunk_count": len(hunks),
            "symbols_in_hunks": symbols_in_hunks[:limit],
            "symbols_added": (compare.get("result") or {}).get("symbols_added") or [],
            "symbols_removed": (compare.get("result") or {}).get("symbols_removed")
            or [],
            "direct": direct,
            "transitive": transitive[:limit],
            "related_tests": unique_tests[:limit],
            "truncated": truncated,
        },
        evidence=evidence[: limit * 3],
        limitations=limitations,
    )


def _count_evidence_statuses(evidence: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(e.get("status") or "unknown") for e in evidence))


def _normalize_verify_state(verify: dict[str, Any] | None) -> dict[str, Any]:
    if not verify:
        return {
            "state": "omitted",
            "automation_verified": False,
            "execution": [],
        }
    result = verify.get("result") or {}
    state = str(result.get("state") or "unknown")
    execution = list(result.get("execution") or [])
    verified_steps = [e for e in execution if e.get("status") == "verified"]
    skipped_steps = [e for e in execution if e.get("status") == "skipped"]
    failed_steps = [e for e in execution if e.get("status") == "failed"]
    automation_verified = bool(
        result.get("automation_verified")
        if "automation_verified" in result
        else (state == "verified" and verified_steps and not failed_steps)
    )
    skipped_only = bool(result.get("skipped_only")) or (
        state == "verified" and not verified_steps and bool(skipped_steps) and not failed_steps
    )
    display_state = state
    if state == "blocked":
        display_state = "blocked"
    elif state == "planned":
        display_state = "blocked"
    elif skipped_only:
        display_state = "verified (skipped-only — not human review)"
    elif state == "verified":
        display_state = "verified (automation only — not human review)"
    return {
        "state": display_state,
        "raw_state": state,
        "automation_verified": automation_verified,
        "skipped_only": skipped_only,
        "execution": execution,
        "verified_count": len(verified_steps),
        "skipped_count": len(skipped_steps),
        "failed_count": len(failed_steps),
        "envelope_status": verify.get("status"),
    }


def apply_contradicted_on_verify_failure(
    impact: dict[str, Any], verify: dict[str, Any] | None
) -> dict[str, Any]:
    """Attach contradicted evidence when automation verify steps failed."""
    if not verify:
        return impact
    result = verify.get("result") or {}
    failed = [
        e
        for e in (result.get("execution") or [])
        if e.get("status") == "failed"
    ]
    if not failed:
        return impact
    evidence = list(impact.get("evidence") or [])
    for step in failed:
        evidence.append(
            {
                "type": "verification_contradiction",
                "status": "contradicted",
                "step_id": step.get("step_id"),
                "detail": "Verify step failed — prior derived impact is not proof of safety",
            }
        )
    out = dict(impact)
    out["evidence"] = evidence
    limits = list(out.get("limitations") or [])
    limits.append(
        "CONTRADICTED: one or more verify steps failed; do not treat derived impact as clean"
    )
    out["limitations"] = limits
    return out


def evaluate_pr_gate_exit(
    payload: dict[str, Any], *, strict: bool = False
) -> int:
    """Return process exit code. Default fail-open; --strict hardens."""
    if payload.get("status") == "failed":
        return 1
    if not strict:
        return 0
    impact = payload.get("impact") or payload
    if impact.get("status") == "failed":
        return 1
    verify = payload.get("verify_norm") or {}
    if verify.get("raw_state") == "failed" or verify.get("failed_count"):
        return 1
    evidence = impact.get("evidence") or []
    if any(e.get("status") == "uncertain" for e in evidence):
        return 1
    if any(e.get("status") == "contradicted" for e in evidence):
        return 1
    return 0


def render_pr_gate_markdown(payload: dict[str, Any]) -> str:
    """Render a sticky-PR-comment body from a pr-gate payload."""
    impact = payload.get("impact") or payload
    result = impact.get("result") or {}
    verify = payload.get("verify_norm") or _normalize_verify_state(
        payload.get("verify")
    )
    repo = impact.get("repository") or {}
    evidence = list(impact.get("evidence") or [])
    counts = _count_evidence_statuses(evidence)
    lines: list[str] = []
    lines.append("## Witnis PR evidence gate")
    lines.append("")
    lines.append(
        "> Evidence-backed blast radius for this PR. "
        "Statuses are auditable; verify is gated. "
        "Harnis is a stdio MCP seatbelt — not an OS sandbox."
    )
    lines.append("")

    if repo.get("index_stale") or counts.get("stale"):
        lines.append("### STALE index")
        lines.append("")
        lines.append(
            f"Indexed revision `{repo.get('indexed_revision')}` differs from live "
            f"`{repo.get('revision')}`. Re-run `witnis index` before trusting edges."
        )
        lines.append("")

    lines.append("### Scope")
    lines.append("")
    lines.append(f"- **analysis_scope:** `{result.get('analysis_scope') or 'unknown'}`")
    lines.append(f"- **base:** `{((result.get('base') or {}).get('hash')) or repo.get('base')}`")
    lines.append(f"- **head:** `{((result.get('head') or {}).get('hash')) or repo.get('head')}`")
    lines.append(
        f"- **merge_base:** `{((result.get('merge_base') or {}).get('hash')) or repo.get('merge_base')}`"
    )
    lines.append(
        f"- **files:** {result.get('file_count', len(result.get('files') or []))}"
    )
    lines.append("")

    lines.append("### Observed files")
    lines.append("")
    files = result.get("files") or []
    if not files:
        lines.append("_No file changes in three-dot range._")
    else:
        for row in files[:40]:
            lines.append(f"- `{row.get('status')}` `{row.get('path')}`")
        if len(files) > 40:
            lines.append(f"- … and {len(files) - 40} more")
    lines.append("")

    lines.append("### Derived impact")
    lines.append("")
    hunk_syms = result.get("symbols_in_hunks") or []
    lines.append(f"- **symbols in hunks:** {len(hunk_syms)}")
    for s in hunk_syms[:15]:
        lines.append(
            f"  - `{s.get('name')}` (`{s.get('file_path')}`:{s.get('start_line')})"
        )
    direct = result.get("direct") or []
    lines.append(f"- **direct edges:** {len(direct)}")
    for e in direct[:12]:
        lines.append(
            f"  - `{e.get('relation_type')}` `{e.get('source')}` → `{e.get('target')}`"
        )
    tests = result.get("related_tests") or []
    lines.append(f"- **related tests (heuristic):** {len(tests)}")
    for t in tests[:10]:
        lines.append(f"  - `{t.get('name')}` (`{t.get('file_path')}`)")
    lines.append("")

    lines.append("### Evidence status counts")
    lines.append("")
    if not counts:
        lines.append("_No evidence items._")
    else:
        for key in sorted(counts):
            lines.append(f"- **{key}:** {counts[key]}")
    lines.append("")
    lines.append(
        "<details><summary>Status legend</summary>\n\n"
        "- `observed` — seen in git/index\n"
        "- `derived` — inferred from relations/hunks\n"
        "- `verified` — an allowlisted automation step passed\n"
        "- `automation_verified` — verify state after gated execute (not human sign-off)\n"
        "- `unverified` / `uncertain` — weak or incomplete signal\n"
        "- `stale` — index revision drifted from HEAD\n"
        "- `contradicted` — verify failure undercuts prior comfort\n"
        "- `skipped` — step not executed (never means human reviewed)\n"
        "\n</details>"
    )
    lines.append("")

    lines.append("### Limitations / unknowns")
    lines.append("")
    for lim in impact.get("limitations") or []:
        lines.append(f"- {lim}")
    if not impact.get("limitations"):
        lines.append("- _(none listed)_")
    lines.append("")

    lines.append("### Verify")
    lines.append("")
    lines.append(f"- **state:** `{verify.get('state')}`")
    if verify.get("raw_state") and verify.get("raw_state") != verify.get("state"):
        lines.append(f"- **engine raw_state:** `{verify.get('raw_state')}`")
    lines.append(
        f"- **automation_verified:** `{verify.get('automation_verified')}` "
        "(never claim human review from this flag)"
    )
    execution = verify.get("execution") or []
    if execution:
        lines.append("")
        lines.append("| step | status | notes |")
        lines.append("| --- | --- | --- |")
        for step in execution:
            note = step.get("reason") or step.get("exit_code") or ""
            lines.append(
                f"| `{step.get('step_id')}` | `{step.get('status')}` | {note} |"
            )
        if verify.get("skipped_count"):
            lines.append("")
            lines.append(
                f"_Note: {verify.get('skipped_count')} step(s) marked `skipped` "
                "— these are not human reviews._"
            )
    elif verify.get("state") == "blocked":
        lines.append("")
        lines.append(
            "Execution **blocked** (needs `--execute` and `WITNIS_ALLOW_VERIFY=1`). "
            "Plan-only / CI default is correct."
        )
    elif verify.get("state") == "omitted":
        lines.append("")
        lines.append("Verify not requested for this run (`--with-plan` / execute flags).")
    lines.append("")

    lines.append("### Trusted Agent Loop")
    lines.append("")
    lines.append(
        "1. **Witnis** — impact + evidence envelopes  \n"
        "2. **PR gate** — this comment  \n"
        "3. **Gated verify** — authorize explicitly  \n"
        "4. **Harnis** — stdio MCP seatbelt (wrap `witnis mcp`; optional editor hooks)  \n"
    )
    lines.append("")
    lines.append(
        "Docs: `docs/trusted-agent-loop.md` · Partner: "
        "[Harnis](https://github.com/L00PLeGeNd/Harnis)"
    )
    lines.append("")
    return "\n".join(lines)


def run_pr_gate(
    db_path: Path,
    *,
    base_ref: str,
    head_ref: str = "HEAD",
    root: Path | None = None,
    reindex: bool = True,
    with_plan: bool = True,
    execute_verify: bool = False,
    limit: int = 50,
    strict: bool = False,
) -> dict[str, Any]:
    """Build full PR gate payload (impact + optional plan/verify + markdown)."""
    if reindex and root is not None:
        index_repository(root, db_path, incremental=True)

    impact = analyze_pr_impact(
        db_path, base_ref=base_ref, head_ref=head_ref, limit=limit
    )
    verify_payload: dict[str, Any] | None = None
    if with_plan or execute_verify:
        head_hash = ((impact.get("result") or {}).get("head") or {}).get("hash")
        focus = None
        syms = (impact.get("result") or {}).get("symbols_in_hunks") or []
        if syms:
            focus = str(syms[0].get("name") or "") or None
        if execute_verify:
            verify_payload = run_verification(
                db_path,
                execute=True,
                target=focus,
                revision=head_hash or head_ref,
            )
        else:
            verify_payload = create_verification_plan(
                db_path, target=focus, revision=head_hash or head_ref
            )
            # Force blocked semantics for plan-only in gate context
            if not execute_verify:
                verify_payload = dict(verify_payload)
                result = dict(verify_payload.get("result") or {})
                if result.get("state") == "planned":
                    result["state"] = "blocked"
                    verify_payload["result"] = result
                    verify_payload["status"] = "partial"
                    limits = list(verify_payload.get("limitations") or [])
                    limits.append(
                        "PR gate default: verify not executed (blocked until authorized)"
                    )
                    verify_payload["limitations"] = limits

    impact = apply_contradicted_on_verify_failure(impact, verify_payload)
    verify_norm = _normalize_verify_state(verify_payload)
    payload = {
        "status": impact.get("status"),
        "impact": impact,
        "verify": verify_payload,
        "verify_norm": verify_norm,
        "strict": strict,
    }
    payload["markdown"] = render_pr_gate_markdown(payload)
    payload["exit_code"] = evaluate_pr_gate_exit(payload, strict=strict)
    return payload
