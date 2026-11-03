# Public benchmark methodology (Witnis)

Repo: https://github.com/L00PLeGeNd/Witnis

## Goal

Publish **reproducible**, fixture-backed comparisons so agents and humans can verify Witnis claims without vibes.

## Suites

| Suite | Command | Fixture(s) |
|---|---|---|
| Local regression | `python -m witnis bench --suite local` | `fixtures/mini_py` (`benchmarks/tasks.json`) |
| Public acceptance | `python -m witnis bench --suite public` | `mini_py` + Go checks (`benchmarks/public/tasks.json`) |
| Baseline deltas | `python -m witnis compare-baselines fixtures/mini_py` | git-grep / naive scan vs Witnis |

## Metrics

1. **Typed symbol recall** — search returns named symbols with file+line (not just text hits)
2. **Call/impact edges** — trace/impact return relation edges baselines cannot
3. **Evidence envelopes** — every answer carries `evidence` + `limitations`
4. **Verify gate** — unauthorized execution stays `blocked`
5. **Index health** — zero structural issues on fixtures
6. **LSP enrichment** (optional) — Jedi definitions/refs when `witnis[lsp]` installed
7. **Multi-language smoke** — Go fixture symbols/imports/calls indexed
8. **Latency** — reported in baseline compare (informational)

## Baselines compared

- **git grep / naive text scan** — text hits, no symbol kinds / call graph / evidence
- **Naive regex defs** — shallow `def/class` guess
- **Naked agent / RAG** — not auto-run here; document qualitative gap: no gated verify, no typed evidence statuses

## Reproducibility

```bash
pip install -e ".[dev,lsp]"
pytest -q
python -m witnis bench --suite local
python -m witnis bench --suite public
python -m witnis compare-baselines fixtures/mini_py --out docs/benchmarks/local-v1.md
```

## Expansion path

- Add larger public corpora (Apache-licensed sample repos) under `fixtures/public_*`
- Record machine class + OS in report JSON
- Track score history in CI against `benchmarks/public/tasks.json`
