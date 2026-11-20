"""A/B analysis comparison harness (measurable without an LLM).

Arm A — grep / path heuristics (what a bare agent often starts with).
Arm B — Witnis index evidence (search + callers + impact + related tests).

Agent task-success / token cost still need human+model runs; this harness
publishes the *analysis completeness* gap the community can reproduce today.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from witnis.core.index import index_repository
from witnis.core.tools import analyze_impact, find_related_tests, repo_search, trace_symbol


@dataclass
class ArmResult:
    arm: str
    task_id: str
    seconds: float
    symbols_found: list[str] = field(default_factory=list)
    callers_found: list[str] = field(default_factory=list)
    tests_found: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _grep_arm(corpus: Path, needle: str) -> ArmResult:
    t0 = time.perf_counter()
    symbols: list[str] = []
    callers: list[str] = []
    tests: list[str] = []
    pat = re.compile(re.escape(needle))
    for path in corpus.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".java", ".go", ".ts", ".js"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(corpus).as_posix()
        if needle in text:
            if "test" in rel.lower():
                tests.append(rel)
            for i, line in enumerate(text.splitlines(), 1):
                if pat.search(line):
                    symbols.append(f"{rel}:{i}:{line.strip()[:80]}")
                    # crude "caller" = any other line in other files mentioning needle
    # second pass: files that reference needle but are not the def line only
    for path in corpus.rglob("*.py"):
        rel = path.relative_to(corpus).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle in text and "def " + needle not in text and f"def {needle}" not in text:
            callers.append(rel)
    elapsed = time.perf_counter() - t0
    return ArmResult(
        arm="A_grep",
        task_id=needle,
        seconds=round(elapsed, 4),
        symbols_found=symbols[:20],
        callers_found=sorted(set(callers))[:20],
        tests_found=sorted(set(tests))[:20],
        notes=["text hits only — no typed callers, no impact edges, no verify gate"],
    )


def _witnis_arm(corpus: Path, db: Path, needle: str) -> ArmResult:
    t0 = time.perf_counter()
    index_repository(corpus, db, incremental=False)
    search = repo_search(db, query=needle, limit=20)
    trace = trace_symbol(db, name=needle)
    impact = analyze_impact(db, target=needle)
    tests = find_related_tests(db, target=needle)
    elapsed = time.perf_counter() - t0
    matches = (search.get("result") or {}).get("matches") or []
    callers = (trace.get("result") or {}).get("called_by") or []
    related = (tests.get("result") or {}).get("tests") or []
    direct = (impact.get("result") or {}).get("direct") or []
    caller_names = [str(c.get("source")) for c in callers]
    for edge in direct:
        src = str(edge.get("source") or "")
        if src and src not in caller_names:
            caller_names.append(src)
    return ArmResult(
        arm="B_witnis",
        task_id=needle,
        seconds=round(elapsed, 4),
        symbols_found=[
            f"{m.get('file_path')}:{m.get('start_line')}:{m.get('name')}" for m in matches
        ],
        callers_found=caller_names,
        tests_found=sorted(
            {str(t.get("file_path")) for t in related if t.get("file_path")}
        ),
        notes=[
            f"impact_direct_edges={len(direct)}",
            "typed search + callers + related tests + verify plan available",
        ],
    )


def compare_task(
    corpus: Path,
    work: Path,
    *,
    task_id: str,
    needle: str,
    expect_callers_substr: list[str] | None = None,
    expect_tests_substr: list[str] | None = None,
) -> dict[str, Any]:
    a = _grep_arm(corpus, needle)
    b = _witnis_arm(corpus, work / f"{task_id}.sqlite", needle)

    def recall(found: list[str], expect: list[str] | None) -> float | None:
        if not expect:
            return None
        hits = 0
        for exp in expect:
            if any(exp.lower() in f.lower() for f in found):
                hits += 1
        return hits / len(expect)

    return {
        "task_id": task_id,
        "needle": needle,
        "arm_a": a.as_dict(),
        "arm_b": b.as_dict(),
        "caller_recall_a": recall(a.callers_found, expect_callers_substr),
        "caller_recall_b": recall(b.callers_found, expect_callers_substr),
        "test_recall_a": recall(a.tests_found, expect_tests_substr),
        "test_recall_b": recall(b.tests_found, expect_tests_substr),
        "delta_notes": [
            "Arm B should expose typed callers/tests; Arm A is string presence only.",
            "Full agent success/token metrics require the human+model protocol.",
        ],
    }


def run_pack(repo_root: Path, pack_path: Path, work: Path) -> dict[str, Any]:
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    results = []
    for task in pack.get("tasks") or []:
        corpus = (repo_root / task["corpus"]).resolve()
        results.append(
            compare_task(
                corpus,
                work,
                task_id=task["id"],
                needle=task["needle"],
                expect_callers_substr=task.get("expect_callers_substr"),
                expect_tests_substr=task.get("expect_tests_substr"),
            )
        )
    return {
        "pack": pack.get("id"),
        "title": pack.get("title"),
        "disclaimer": pack.get("disclaimer"),
        "results": results,
    }
