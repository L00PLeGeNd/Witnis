from __future__ import annotations

from pathlib import Path

from witnis.bench import run_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_suite_passes(tmp_path: Path) -> None:
    report = run_benchmark(
        ROOT,
        ROOT / "benchmarks" / "tasks.json",
        tmp_path / "bench.sqlite",
    )
    assert report["total"] == 30
    assert report["passed"] == report["total"], report
