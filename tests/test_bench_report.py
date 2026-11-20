from __future__ import annotations

from pathlib import Path

from witnis.bench import run_benchmark
from witnis.core.bench_report import format_github_step_summary, write_bench_report_html

ROOT = Path(__file__).resolve().parents[1]


def test_write_bench_report_html(tmp_path: Path) -> None:
    report = run_benchmark(
        ROOT,
        ROOT / "benchmarks" / "tasks.json",
        tmp_path / "bench.sqlite",
    )
    out = tmp_path / "report.html"
    path = write_bench_report_html(report, out, suite="local")
    html = path.read_text(encoding="utf-8")
    assert "Witnis bench" in html
    assert "pass" in html
    assert str(report["passed"]) in html
    summary = format_github_step_summary(report, suite="local")
    assert "passed" in summary
    assert report["results"][0]["id"] in summary
    assert "miss-cases.md" in summary
    assert "miss-cases.md" in html
