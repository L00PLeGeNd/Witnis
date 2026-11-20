"""Render benchmark run results as HTML / Markdown / Actions summary."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_bench_report_html(
    report: dict[str, Any],
    out: Path,
    *,
    suite: str = "public",
    title: str | None = None,
) -> Path:
    """Write a self-contained HTML bench report page."""
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    passed = int(report.get("passed") or report.get("tp") or 0)
    total = int(report.get("total") or report.get("cases") or 0)
    # ground-truth aggregate uses tp/fn without total tasks the same way
    if "score" in report:
        score = float(report.get("score") or 0.0)
    elif total:
        score = passed / total
    else:
        score = 0.0
    rows = report.get("results") or report.get("reports") or []
    heading = title or f"Witnis bench · {suite}"
    row_html: list[str] = []
    if report.get("results"):
        for r in report["results"]:
            ok = bool(r.get("passed"))
            row_html.append(
                "<tr>"
                f"<td class='mono'>{html.escape(str(r.get('id') or ''))}</td>"
                f"<td class='{'ok' if ok else 'bad'}'>{'pass' if ok else 'fail'}</td>"
                f"<td class='mono'>{html.escape(str(r.get('detail') or '')[:240])}</td>"
                "</tr>"
            )
    elif report.get("reports"):
        for r in report["reports"]:
            cid = str(r.get("case_id") or r.get("id") or "")
            status = str(r.get("status") or ("ok" if r.get("metrics") else "n/a"))
            row_html.append(
                "<tr>"
                f"<td class='mono'>{html.escape(cid)}</td>"
                f"<td>{html.escape(status)}</td>"
                f"<td class='mono'>{html.escape(json.dumps(r.get('metrics') or [])[:240])}</td>"
                "</tr>"
            )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(heading)}</title>
  <style>
    :root {{
      --ink: #121c18; --muted: #5a6a63; --line: rgba(18,28,24,.14);
      --ok: #0c5c48; --bad: #8f2d2d; --paper: #eef3f0;
    }}
    body {{
      margin: 0; font-family: "Segoe UI", system-ui, sans-serif; color: var(--ink);
      background: linear-gradient(180deg, #f6f9f7, var(--paper));
    }}
    main {{ max-width: 920px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }}
    h1 {{ font-size: 1.75rem; letter-spacing: -0.03em; margin: 0 0 .5rem; }}
    .meta {{ color: var(--muted); font-size: .9rem; margin-bottom: 1.5rem; }}
    .stats {{ display: flex; gap: 1.25rem; flex-wrap: wrap; margin-bottom: 1.5rem; }}
    .stat {{ border-top: 1px solid var(--line); padding-top: .55rem; min-width: 5.5rem; }}
    .stat .k {{ font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
    .stat .v {{ font-family: ui-monospace, monospace; font-size: 1.4rem; margin-top: .2rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
    th, td {{ text-align: left; padding: .55rem .2rem; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
    .mono {{ font-family: ui-monospace, monospace; font-size: .8rem; }}
    .ok {{ color: var(--ok); font-weight: 600; }}
    .bad {{ color: var(--bad); font-weight: 600; }}
    .note {{ margin-top: 1.5rem; color: var(--muted); font-size: .85rem; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(heading)}</h1>
    <p class="meta">generated {_utc_now()} · acceptance smoke, not corpus leadership · see FAILURE_CASES.md</p>
    <div class="stats">
      <div class="stat"><div class="k">passed</div><div class="v">{passed}</div></div>
      <div class="stat"><div class="k">total</div><div class="v">{total or len(rows)}</div></div>
      <div class="stat"><div class="k">score</div><div class="v">{score:.2f}</div></div>
    </div>
    <table>
      <thead><tr><th>id</th><th>result</th><th>detail</th></tr></thead>
      <tbody>
        {''.join(row_html) or '<tr><td colspan="3">no rows</td></tr>'}
      </tbody>
    </table>
    <p class="note">Public suite proves contracts on fixtures. Known misses: docs/benchmarks/miss-cases.md · FAILURE_CASES.md. PetClinic human-v2 P/R: docs/benchmarks/petclinic-human-v2.md.</p>
  </main>
</body>
</html>
"""
    out.write_text(page, encoding="utf-8")
    return out


def format_github_step_summary(report: dict[str, Any], *, suite: str) -> str:
    """Markdown for $GITHUB_STEP_SUMMARY."""
    passed = int(report.get("passed") or 0)
    total = int(report.get("total") or 0)
    score = float(report.get("score") or (passed / total if total else 0.0))
    lines = [
        f"### Witnis bench (`{suite}`)",
        "",
        f"- **passed:** {passed} / {total}",
        f"- **score:** {score:.2f}",
        "",
        "| id | result |",
        "| --- | --- |",
    ]
    for r in report.get("results") or []:
        mark = "pass" if r.get("passed") else "fail"
        lines.append(f"| `{r.get('id')}` | {mark} |")
    if not report.get("results") and report.get("suite") == "ground-truth":
        lines.append(
            f"| ground-truth | tp={report.get('tp')} fn={report.get('fn')} "
            f"P={report.get('precision')} R={report.get('recall')} |"
        )
    lines.append("")
    lines.append(
        "_Acceptance smoke — not semantic leadership. "
        "Known misses: docs/benchmarks/miss-cases.md · docs/FAILURE_CASES.md._"
    )
    return "\n".join(lines)
