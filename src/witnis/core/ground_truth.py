"""Evaluate labeled ground-truth cases against an indexed store.

Returns precision/recall style metrics — never inflates unknowns into passes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from witnis.core.index import index_repository
from witnis.core.store import Store


@dataclass
class Metric:
    name: str
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float | None:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
        }


@dataclass
class CaseReport:
    case_id: str
    corpus: str
    tasks: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "corpus": self.corpus,
            "tasks": self.tasks,
            "metrics": [m.as_dict() for m in self.metrics],
        }


def _norm(s: str) -> str:
    return str(s).replace("\\", "/").lower()


def _edge_hit(edges: list[dict], source: str, target: str, rel: str) -> bool:
    s_n, t_n, r_n = _norm(source), _norm(target), _norm(rel)
    for e in edges:
        if _norm(e.get("relation_type") or "") != r_n:
            continue
        src = _norm(e.get("source") or "")
        tgt = _norm(e.get("target") or "")
        if s_n in src and t_n in tgt:
            return True
        # allow bare names
        if source.split(".")[-1].lower() in src and target.split(".")[-1].lower() in tgt:
            return True
    return False


def _symbol_hit(hits: list[dict], name: str, path_suffix: str | None) -> bool:
    for h in hits:
        hit_name = h.get("name") or ""
        if hit_name != name and name not in hit_name:
            continue
        if not path_suffix:
            return True
        path = h.get("path") or h.get("file_path") or ""
        if _norm(path_suffix) in _norm(path):
            return True
    return False


def evaluate_case(label: dict[str, Any], repo_root: Path, db_path: Path) -> CaseReport:
    index_repository(repo_root, db_path, incremental=False)
    store = Store(db_path)
    report = CaseReport(case_id=str(label.get("id")), corpus=str(label.get("corpus")))
    sym_m = Metric("symbol_locate")
    edge_m = Metric("call_edge")
    try:
        all_edges = store.list_relations(limit=5000)
        for task in label.get("tasks") or []:
            kind = task.get("kind")
            expect = task.get("expect") or {}
            detail: dict[str, Any] = {"id": task.get("id"), "kind": kind, "ok": False}
            if kind == "symbol_locate":
                query = str(task.get("query") or "")
                hits = store.search(query, limit=50)
                wanted = expect.get("symbols") or []
                for w in wanted:
                    name = w.get("name") or ""
                    path = w.get("path")
                    if _symbol_hit(hits, name, path):
                        sym_m.tp += 1
                        detail["ok"] = True
                    else:
                        sym_m.fn += 1
                detail["hits"] = hits[:10]
            elif kind in {"call_edge"}:
                wanted = expect.get("edges") or []
                ok_all = True
                for w in wanted:
                    rel = w.get("relation_type") or "calls"
                    # map injects/implements into same edge metric bucket
                    hit = _edge_hit(
                        all_edges,
                        str(w.get("source") or ""),
                        str(w.get("target") or ""),
                        str(rel),
                    )
                    if hit:
                        edge_m.tp += 1
                    else:
                        edge_m.fn += 1
                        ok_all = False
                detail["ok"] = ok_all
            elif kind == "verify_false_pass":
                detail["ok"] = False
                detail["skipped"] = "false-pass harness not executed in offline GT"
            else:
                detail["skipped"] = f"kind {kind} not evaluated yet"
            report.tasks.append(detail)
        report.metrics = [sym_m, edge_m]
    finally:
        store.close()
    return report


def load_label(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_ground_truth_suite(
    *,
    labels_dir: Path,
    repo_root: Path,
    work_dir: Path,
) -> dict[str, Any]:
    """Run all label JSON files under labels_dir; corpora paths are relative to repo_root."""
    reports: list[dict[str, Any]] = []
    label_files = sorted(labels_dir.glob("*.json"))
    for path in label_files:
        label = load_label(path)
        corpus_rel = label.get("corpus") or ""
        corpus_path = (repo_root / corpus_rel).resolve()
        if not corpus_path.is_dir():
            reports.append(
                {
                    "case_id": label.get("id"),
                    "status": "failed",
                    "error": f"corpus missing: {corpus_rel}",
                }
            )
            continue
        db = work_dir / f"{path.stem}.sqlite"
        rep = evaluate_case(label, corpus_path, db)
        reports.append(rep.as_dict())

    # Aggregate
    tp = fp = fn = 0
    for r in reports:
        for m in r.get("metrics") or []:
            tp += int(m.get("tp") or 0)
            fp += int(m.get("fp") or 0)
            fn += int(m.get("fn") or 0)
    precision = (tp / (tp + fp)) if (tp + fp) else None
    recall = (tp / (tp + fn)) if (tp + fn) else None
    return {
        "suite": "ground-truth",
        "cases": len(reports),
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "reports": reports,
    }
