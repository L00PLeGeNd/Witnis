# Ground-truth benchmarks (scaffold)

Status: **scaffold only**. No public “accuracy %” until labeled corpora land.

## Purpose

Upgrade from acceptance checks (`benchmarks/public/tasks.json`) to **labeled** evaluation:

| Task | Metric |
|---|---|
| Symbol location | Precision / Recall |
| Cross-file call edges | Edge Precision / Recall |
| Impact set | Impact Recall |
| Evidence anchors | Evidence Accuracy |
| Gated verify | **False Pass Rate** (critical) |
| Agent assist (later) | Task success / token cost |

## Layout

```
benchmarks/ground-truth/
  schema.json          # task + label schema
  README.md            # this file
  corpora/             # fixed-commit checkouts or vendored slices (future)
  labels/              # human-reviewed expected symbols/edges
  reports/             # generated metric JSON (gitignored locally if large)
```

## Rules

1. Every corpus pins a **commit SHA** (or vendored snapshot with LICENSE).
2. Labels are reviewed; machine guesses are not ground truth.
3. Report unknowns and failures — never inflate “verified”.
4. Acceptance suite (`public`) stays for CI smoke; ground-truth is for depth claims.

## First corpora (planned)

- Python: small FastAPI/Flask slice
- Java: Spring-style DI slice (`fixtures/semantic_java_di` as synthetic start)
- TypeScript: small service slice
- Optional: Spring PetClinic at a fixed tag (separate LICENSE handling)

## Runner (future)

```bash
# not implemented yet — placeholder contract
witnis bench --suite ground-truth
```
