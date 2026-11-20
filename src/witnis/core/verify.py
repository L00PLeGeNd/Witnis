from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.security import assert_path_in_root, redact_text
from witnis.core.tools import (
    analyze_change_impact,
    analyze_impact,
    check_import_graph,
    check_python_syntax,
    explain_change,
    find_related_tests,
    _open_store,
    _repo_meta,
)


def _report_path(db_path: Path) -> Path:
    return db_path.parent / "last_verification.json"


def _save_report(db_path: Path, payload: dict[str, Any]) -> None:
    path = _report_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _persist_run(db_path: Path, payload: dict[str, Any]) -> None:
    """Store verification run + evidence rows for later get_evidence filters."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return
        result = payload.get("result") or {}
        run_id = store.insert_verification_run(
            int(repo["id"]),
            plan_id=result.get("plan_id"),
            target=result.get("target"),
            revision=result.get("revision"),
            state=str(result.get("state") or "unknown"),
            report=payload,
        )
        focus = result.get("target")
        items = []
        for item in payload.get("evidence") or []:
            row = dict(item)
            if focus and not row.get("source_ref"):
                row["source_ref"] = focus
            items.append(row)
        if items:
            store.insert_evidence_items(int(repo["id"]), items, run_id=run_id)
        execution = result.get("execution") or []
        test_rows = [
            step
            for step in execution
            if step.get("step_id") in {"run_tests", "static_compile", "syntax_check", "import_graph"}
            or step.get("exit_code") is not None
        ]
        if test_rows:
            store.insert_test_results(int(repo["id"]), test_rows, run_id=run_id)
    finally:
        store.close()


def create_verification_plan(
    db_path: Path,
    *,
    target: str | None = None,
    revision: str | None = None,
) -> dict[str, Any]:
    """Build a read-only verification plan (does not execute anything)."""
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

    repository = _repo_meta(repo)
    root = Path(repo["root_path"])
    steps: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    limitations = [
        "Plan only — no commands are executed",
        "Execution requires explicit authorization (witnis verify --execute)",
    ]

    change = None
    change_impact = None
    if revision:
        change = explain_change(db_path, revision=revision)
        evidence.extend(change.get("evidence", [])[:10])
        files = [f.get("path") for f in change.get("result", {}).get("files", [])]
        steps.append(
            {
                "id": "review_diff",
                "kind": "manual",
                "description": f"Review git changes for {revision}",
                "files": files,
            }
        )
        change_impact = analyze_change_impact(db_path, revision=revision)
        evidence.extend(change_impact.get("evidence", [])[:15])
        steps.append(
            {
                "id": "change_impact_review",
                "kind": "analysis",
                "description": f"Review hunk-level change impact for {revision}",
                "symbol_count": len(
                    change_impact.get("result", {}).get("symbols_in_hunks") or []
                ),
                "direct_count": len(change_impact.get("result", {}).get("direct") or []),
            }
        )

    impact = None
    tests: list[dict[str, Any]] = []
    focus = target
    if not focus and change:
        hunk_syms = change.get("result", {}).get("symbols_in_hunks") or []
        touched = change.get("result", {}).get("symbols_in_touched_files") or []
        preferred = hunk_syms or touched
        # Prefer method/function symbols over broad class names when present.
        ranked = sorted(
            preferred,
            key=lambda s: (
                0 if s.get("kind") in {"method", "function"} else 1,
                -len(str(s.get("name") or "")),
            ),
        )
        if ranked:
            focus = ranked[0].get("name")
    if focus:
        impact = analyze_impact(db_path, focus)
        evidence.extend(impact.get("evidence", [])[:10])
        tests_payload = find_related_tests(db_path, focus)
        tests = list(tests_payload.get("result", {}).get("tests", []))
        evidence.extend(tests_payload.get("evidence", [])[:5])
        steps.append(
            {
                "id": "impact_review",
                "kind": "analysis",
                "description": f"Review impact for {focus}",
                "direct_count": len(impact.get("result", {}).get("direct", [])),
            }
        )
    # Merge tests discovered via change-impact (revision plans).
    if change_impact:
        for t in change_impact.get("result", {}).get("related_tests") or []:
            tests.append(t)

    test_paths = sorted(
        {
            str(t.get("file_path"))
            for t in tests
            if str(t.get("file_path") or "").endswith(".py")
        }
    )
    if not test_paths and (root / "tests").is_dir():
        test_paths = ["tests"]
        limitations.append("No symbol-linked tests found; falling back to tests/ directory")

    # Static: byte-compile related Python files (or whole tree fallback)
    compile_targets: list[str] = []
    if focus:
        impact_paths: set[str] = set()
        for row in (impact or {}).get("result", {}).get("definitions", []) or []:
            p = row.get("file_path") or row.get("path")
            if p and str(p).endswith(".py"):
                impact_paths.add(str(p))
        store = _open_store(db_path)
        try:
            for hit in store.search(focus, limit=20):
                p = hit.get("file_path") or hit.get("path")
                if p and str(p).endswith(".py"):
                    impact_paths.add(str(p))
        finally:
            store.close()
        compile_targets = sorted(impact_paths)
    if not compile_targets:
        compile_targets = ["."]
        limitations.append("No symbol-linked .py paths; compileall falls back to repo root")

    steps.append(
        {
            "id": "static_compile",
            "kind": "static",
            "description": "Byte-compile related Python sources",
            "command": [sys.executable, "-m", "compileall", "-q", *compile_targets],
            "cwd": str(root),
        }
    )

    syntax_paths = [p for p in compile_targets if p != "." and str(p).endswith(".py")]
    steps.append(
        {
            "id": "syntax_check",
            "kind": "syntax",
            "description": "AST-parse related Python sources",
            "command": None,
            "paths": syntax_paths or None,
        }
    )

    steps.append(
        {
            "id": "import_graph",
            "kind": "graph",
            "description": "Check indexed import edges against known modules",
            "command": None,
        }
    )

    if test_paths:
        steps.append(
            {
                "id": "run_tests",
                "kind": "pytest",
                "description": "Run related pytest targets",
                "command": [sys.executable, "-m", "pytest", "-q", *test_paths],
                "cwd": str(root),
            }
        )
    else:
        steps.append(
            {
                "id": "run_tests",
                "kind": "pytest",
                "description": "No test targets discovered",
                "command": None,
            }
        )
        limitations.append("No pytest targets discovered for this plan")

    steps.append(
        {
            "id": "static_reindex",
            "kind": "witnis",
            "description": "Re-index after changes and re-check impact",
            "command": ["python", "-m", "witnis", "index", str(root)],
        }
    )

    payload = make_envelope(
        status="success" if steps else "partial",
        repository=repository,
        result={
            "plan_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "target": focus,
            "revision": revision,
            "steps": steps,
            "state": "planned",
            "change_impact": (change_impact or {}).get("result") if change_impact else None,
        },
        evidence=evidence,
        limitations=limitations,
    )
    _save_report(db_path, payload)
    return payload


def run_verification(
    db_path: Path,
    *,
    execute: bool = False,
    target: str | None = None,
    revision: str | None = None,
    timeout_sec: int = 120,
    profile: str | None = None,
) -> dict[str, Any]:
    """Execute an authorized verification plan, or refuse without execute flag."""
    plan = create_verification_plan(db_path, target=target, revision=revision)
    if plan["status"] == "failed":
        return plan

    if not execute:
        plan["result"]["state"] = "blocked"
        plan["limitations"] = list(plan.get("limitations") or []) + [
            "Execution denied: pass execute=true / --execute and set WITNIS_ALLOW_VERIFY=1"
        ]
        plan["status"] = "partial"
        _save_report(db_path, plan)
        return plan

    if os.environ.get("WITNIS_ALLOW_VERIFY") != "1":
        plan["result"]["state"] = "blocked"
        plan["limitations"] = list(plan.get("limitations") or []) + [
            "Set environment variable WITNIS_ALLOW_VERIFY=1 to authorize command execution"
        ]
        plan["status"] = "partial"
        _save_report(db_path, plan)
        return plan

    from witnis.core.verify_isolate import (
        cleanup_verify_workspace,
        create_verify_worktree,
        run_isolated_command,
    )

    root = Path(plan["repository"]["root_path"])
    selected_profile = (
        profile
        or os.environ.get("WITNIS_VERIFY_PROFILE", "worktree").strip().lower()
        or "worktree"
    )
    isolate = os.environ.get("WITNIS_VERIFY_ISOLATE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    work_root = root
    work_meta: dict[str, Any] = {"mode": "inplace", "profile": selected_profile}
    if isolate:
        try:
            work_root, work_meta = create_verify_worktree(root, revision=revision)
            work_meta["profile"] = selected_profile
        except OSError:
            work_root, work_meta = root, {"mode": "inplace", "profile": selected_profile, "error": "worktree_failed"}

    results: list[dict[str, Any]] = []
    try:
        for step in plan["result"].get("steps", []):
            cmd = step.get("command")
            kind = step.get("kind")
            if kind == "graph":
                graph = check_import_graph(db_path)
                broken = graph.get("result", {}).get("broken") or []
                results.append(
                    {
                        "step_id": step.get("id"),
                        "status": "verified" if not broken else "failed",
                        "broken_count": len(broken),
                        "ok": graph.get("result", {}).get("ok"),
                    }
                )
                continue
            if kind == "syntax":
                paths = step.get("paths")
                syntax = check_python_syntax(
                    db_path, paths=paths if isinstance(paths, list) else None
                )
                errors = syntax.get("result", {}).get("errors") or []
                results.append(
                    {
                        "step_id": step.get("id"),
                        "status": "verified" if not errors else "failed",
                        "checked": syntax.get("result", {}).get("checked"),
                        "error_count": len(errors),
                        "errors": errors[:10],
                    }
                )
                continue
            if not cmd or kind not in {"pytest", "static"}:
                results.append(
                    {
                        "step_id": step.get("id"),
                        "status": "skipped",
                        "reason": "non-executable or empty command",
                    }
                )
                continue
            cwd = work_root if isolate else Path(step.get("cwd") or root)
            try:
                assert_path_in_root(work_root if isolate else root, cwd)
            except PermissionError as exc:
                results.append(
                    {
                        "step_id": step.get("id"),
                        "status": "failed",
                        "reason": str(exc),
                    }
                )
                continue
            # allowlist: pytest / python -m pytest / python -m compileall
            py = Path(cmd[0]).name.lower().startswith("python") if cmd else False
            allowed = (
                cmd[0] == "pytest"
                or (len(cmd) >= 3 and py and cmd[1:3] == ["-m", "pytest"])
                or (len(cmd) >= 3 and py and cmd[1:3] == ["-m", "compileall"])
            )
            if not allowed:
                results.append(
                    {
                        "step_id": step.get("id"),
                        "status": "failed",
                        "reason": "command allowlist: pytest / compileall only",
                    }
                )
                continue
            if kind == "static":
                try:
                    for arg in cmd[3:]:
                        if arg.startswith("-"):
                            continue
                        assert_path_in_root(
                            work_root if isolate else root,
                            (cwd / arg).resolve() if arg != "." else cwd,
                        )
                except PermissionError as exc:
                    results.append(
                        {
                            "step_id": step.get("id"),
                            "status": "failed",
                            "reason": str(exc),
                        }
                    )
                    continue
            if isolate:
                out = run_isolated_command(
                    cmd,
                    cwd=cwd,
                    timeout_sec=timeout_sec,
                    allow_network=False,
                    profile=selected_profile,
                )
                if out.get("status") == "timeout":
                    results.append(
                        {
                            "step_id": step.get("id"),
                            "status": "failed",
                            "reason": f"timeout after {timeout_sec}s",
                            "isolation": work_meta,
                            "fs_diff": out.get("fs_diff"),
                        }
                    )
                else:
                    isolation = {
                        **work_meta,
                        "container_runtime": out.get("container_runtime"),
                        "network": out.get("network"),
                    }
                    results.append(
                        {
                            "step_id": step.get("id"),
                            "status": "verified" if out.get("exit_code") == 0 else "failed",
                            "exit_code": out.get("exit_code"),
                            "stdout_tail": redact_text(str(out.get("stdout") or "")[-2000:]),
                            "stderr_tail": redact_text(str(out.get("stderr") or "")[-2000:]),
                            "isolation": isolation,
                            "fs_diff": out.get("fs_diff"),
                            "network": out.get("network"),
                        }
                    )
            else:
                try:
                    proc = subprocess.run(
                        cmd,
                        cwd=str(cwd),
                        capture_output=True,
                        text=True,
                        timeout=timeout_sec,
                        check=False,
                    )
                    results.append(
                        {
                            "step_id": step.get("id"),
                            "status": "verified" if proc.returncode == 0 else "failed",
                            "exit_code": proc.returncode,
                            "stdout_tail": redact_text(proc.stdout[-2000:]),
                            "stderr_tail": redact_text(proc.stderr[-2000:]),
                        }
                    )
                except subprocess.TimeoutExpired:
                    results.append(
                        {
                            "step_id": step.get("id"),
                            "status": "failed",
                            "reason": f"timeout after {timeout_sec}s",
                        }
                    )
    finally:
        if isolate and work_meta.get("mode") in {"worktree", "copy"}:
            cleanup_verify_workspace(root, work_root, work_meta)

    any_fail = any(r.get("status") == "failed" for r in results)
    verified_steps = [r for r in results if r.get("status") == "verified"]
    skipped_steps = [r for r in results if r.get("status") == "skipped"]
    # automation_verified: allowlisted steps passed; skipped never counts as human review
    automation_ok = bool(results) and not any_fail and (
        bool(verified_steps) or bool(skipped_steps)
    )
    evidence = list(plan.get("evidence") or [])
    for item in results:
        evidence.append(
            {
                "type": "verification",
                "status": item.get("status"),
                "step_id": item.get("step_id"),
                "exit_code": item.get("exit_code"),
            }
        )
        if item.get("status") == "failed":
            evidence.append(
                {
                    "type": "verification_contradiction",
                    "status": "contradicted",
                    "step_id": item.get("step_id"),
                    "detail": "Verify step failed",
                }
            )

    if any_fail:
        state = "failed"
    elif automation_ok:
        # Keep state="verified" for contract compat; honesty lives in flags + limitations
        state = "verified"
    else:
        state = "failed"
    payload = make_envelope(
        status="success" if automation_ok and not any_fail else "partial",
        repository=plan.get("repository"),
        result={
            **plan.get("result", {}),
            "state": state,
            "automation_verified": bool(verified_steps) and not any_fail,
            "skipped_only": bool(skipped_steps) and not verified_steps and not any_fail,
            "execution": results,
        },
        evidence=evidence,
        limitations=list(plan.get("limitations") or [])
            + [
                "state=verified here means allowlisted automations passed — not human review",
                "skipped steps are not executed checks",
            ]
        + [
            "Auto-executed: pytest, compileall, syntax AST check, import graph",
            "Stdout/stderr truncated in report",
            (
                f"Isolation mode={work_meta.get('mode')} (worktree/copy + scrubbed env + FS diff); "
                "not a full OS/container sandbox — see SECURITY.md"
            ),
        ],
    )
    _persist_run(db_path, payload)
    _save_report(db_path, payload)
    return payload


def get_verification_report(db_path: Path) -> dict[str, Any]:
    path = _report_path(db_path)
    if not path.exists():
        store = _open_store(db_path)
        try:
            overview = store.overview()
            repo = overview.get("repository")
        finally:
            store.close()
        return make_envelope(
            status="partial",
            repository=_repo_meta(repo) if repo else None,
            result={},
            limitations=["No verification report yet. Run create_verification_plan first."],
        )
    return json.loads(path.read_text(encoding="utf-8"))


def list_verification_runs(db_path: Path, limit: int = 20) -> dict[str, Any]:
    """List persisted verification runs (newest first)."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        runs = store.list_verification_runs(limit=limit) if repo else []
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={"runs": []},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    return make_envelope(
        status="success" if runs else "partial",
        repository=_repo_meta(repo),
        result={"runs": runs, "count": len(runs)},
        evidence=[
            {
                "type": "verification_run",
                "status": r.get("state"),
                "source_ref": r.get("target"),
                "run_id": r.get("id"),
                "captured_at": r.get("captured_at"),
            }
            for r in runs
        ],
        limitations=[] if runs else ["No verification runs persisted yet"],
    )
