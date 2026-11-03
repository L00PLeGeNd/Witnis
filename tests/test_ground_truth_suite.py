from __future__ import annotations

from pathlib import Path

from witnis.core.ground_truth import run_ground_truth_suite

ROOT = Path(__file__).resolve().parents[1]


def test_ground_truth_semantic_java_di(tmp_path: Path) -> None:
    report = run_ground_truth_suite(
        labels_dir=ROOT / "benchmarks" / "ground-truth" / "labels",
        repo_root=ROOT,
        work_dir=tmp_path,
    )
    assert report["cases"] >= 1
    assert report["fn"] == 0, report
    assert (report.get("recall") or 0) >= 0.99
