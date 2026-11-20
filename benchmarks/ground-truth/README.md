# Ground-truth benchmarks

Status: **vendored fixtures green in CI** · **PetClinic human subset labeled** (local checkout required for scoring).

## Purpose

Upgrade from acceptance checks (`benchmarks/public/tasks.json`) to **labeled** evaluation:

| Task | Metric |
|---|---|
| Symbol location | Precision / Recall |
| Cross-file call / inject / inherit edges | Edge Precision / Recall |
| Impact set | **Direct / Indirect** Recall (human GT) |
| Evidence anchors | Evidence Accuracy |
| Gated verify | **False Pass Rate** (critical) |
| Agent assist (later) | Task success / token cost |

## Layout

```
benchmarks/ground-truth/
  schema.json
  LABELING_SHEET.md    # classes + scoreboard + human decisions
  corpora/             # pins + gitignored checkouts/
  labels/              # human + auto + vendored fixtures
  reports/             # generated metric JSON
```

## Rules

1. Every corpus pins a **commit SHA** (or vendored snapshot with LICENSE).
2. Labels are reviewed; machine guesses (`*_auto.json`) are not ground truth.
3. Report unknowns and failures — never inflate “verified”.
4. Acceptance suite (`public`) stays for CI smoke; ground-truth is for depth claims.

## Corpora

| Corpus | Mode | Path |
| --- | --- | --- |
| `semantic_java_di` / `semantic_py_di` | Vendored fixtures | `fixtures/…` |
| spring-petclinic @ `500158f7…` | Auto bootstrap | `labels/spring_petclinic_auto.json` |
| spring-petclinic @ `500158f7…` | **Human-v2 adjudicated (16 tasks)** | `labels/spring_petclinic_human.json` · `adjudication/petclinic-human-v2.md` |

Checkout (gitignored): `corpora/checkouts/spring-petclinic` — see `corpora/spring-petclinic.pin.md`.

## Runner

```bash
witnis bench --suite ground-truth
```

CI scores whatever corpora are present. Without the PetClinic checkout, those label files are **skipped** (not failed). With checkout, Direct/Indirect impact metrics appear under `impact_direct` / `impact_indirect`.
