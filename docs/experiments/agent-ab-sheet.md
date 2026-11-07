# Agent A/B sheet (community-visible)

Fill one row per task after running both arms on the **same** model, prompt, and corpus commit.

```
date  corpus@commit  task  arm  success  correct  omitted_impact  tests  tokens  seconds  notes
----  -------------  ----  ---  -------  -------  --------------  -----  ------  -------  -----
                           A
                           B
```

## Arms

- **A** — Agent only (Claude Code / Codex / …). No Witnis MCP.
- **B** — Same agent + Witnis MCP (`witnis mcp`, `WITNIS_DB` set). Agent must call `look` / impact / verify before claiming done.

## Rules

1. Pin model id + temperature.
2. Same task wording for A and B.
3. Blind grade when possible.
4. Publish raw logs under `benchmarks/experiments/reports/` (gitignored) and a summary PR/issue.

Analysis-only (no LLM) baseline is reproducible via:

```bash
witnis experiment --pack benchmarks/experiments/ab_analysis_pack.json
```
