# PR gate timing notes

Record cold timings when available (machine class + OS). Do not invent numbers.

## Method

```bash
# After cloning spring-petclinic pin (gitignored checkout) or another mid-size tree:
witnis index .
time witnis pr-gate --base <base> --head HEAD --format markdown -o /tmp/pr-gate.md --no-plan
```

## Log

| Date | Repo / SHA | Machine | Index | pr-gate | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-11-18 | spring-petclinic `500158f…` | Windows local | _not re-timed_ | triple-dot helper ~0.04s for `HEAD~10...HEAD` (0 files on this pin depth) | Full index+impact timing still pending on a multi-commit range |
| 2026-11-18 | Witnis CI | GitHub `ubuntu-latest` | via Action | dogfood on PR + push smoke `HEAD~1...HEAD` | Duplicate `pr-gate-dogfood` job key broke 1.10.0 workflow parse; fixed to one PR dogfood + push smoke |

## Caps that affect time

- `impact_symbol_cap` default 20 in `analyze_pr_impact`
- `limit` default 50 for edges / files sample
- Truncation always appears in `limitations[]`
