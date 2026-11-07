# Agent effect experiment protocol (P2)

Goal: measure whether Witnis reduces harmful agent edits versus baseline tools (grep / IDE LSP only).

## Design

- **A — Baseline** — repo checkout + grep / editor search only
- **B — LSP** — + language server (Jedi/Pyright or jdtls)
- **C — Witnis** — + `witnis` MCP/CLI (search, trace, impact, gated verify)

Fixed task pack (10–20 tasks): locate symbol, fix bug, refactor call site, add test, avoid false verify pass.

## Metrics

- **Task success** — Human-graded correct change
- **Omission rate** — Required call sites / files missed
- **False pass rate** — Broken change marked verified
- **Token / wall cost** — Agent spend per task
- **Tool calls** — Count of search/trace/verify

## Rules

1. Pin model + temperature + prompt template across arms.
2. Pin corpus commit SHAs from `benchmarks/ground-truth/corpora/manifest.json`.
3. Blind human grading when possible.
4. Publish raw task logs; never claim leadership from acceptance 21/21 alone.

## Harness status

Scaffold: `benchmarks/experiments/agent_tasks.example.json`  
Runner: not automated yet — execute manually and record CSV under `benchmarks/experiments/reports/` (gitignored).
