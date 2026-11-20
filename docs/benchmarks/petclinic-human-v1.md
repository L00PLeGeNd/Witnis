# PetClinic human-v1 ground truth (subset)

Pinned corpus: [spring-projects/spring-petclinic](https://github.com/spring-projects/spring-petclinic) @ `500158f732419217507c7656904b8e6aa1bcc0d6`  
Labels: [`benchmarks/ground-truth/labels/spring_petclinic_human.json`](../../benchmarks/ground-truth/labels/spring_petclinic_human.json)  
Sheet: [`benchmarks/ground-truth/LABELING_SHEET.md`](../../benchmarks/ground-truth/LABELING_SHEET.md)

**Annotator:** human-v1 (solo). Superseded by **[human-v2 adjudication](petclinic-human-v2.md)** (`label_mode: human_v2_adjudicated`).  
**Not a claim of full-app accuracy** — 14 curated tasks in this pass (v2 adds 2).

## Measured (2026-11-18, local index of the pin)

| Metric | TP | FP | FN | P | R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Symbol locate | 2 | 0 | 0 | 1.0 | 1.0 |
| Call / inject / inherit edges | 9 | 0 | 0 | 1.0 | 1.0 |
| Impact **Direct** | 6 | 0 | 0 | 1.0 | 1.0 |
| Impact **Indirect** | 0 | 0 | 1 | — | **0.0** |

## Honest miss

`Person` → Indirect `OwnerController` (uses `Owner` which inherits `Person`).  
Witnis does not yet emit that typed-use / 2-hop edge in impact packs. Kept in the label so recall stays honest.

Catalogued as **[F1](../FAILURE_CASES.md#f1--typed-use-is-not-a-relation-indirect-fn)** in the failure-case gallery.

## Reproduce

```bash
# checkout already under benchmarks/ground-truth/corpora/checkouts/spring-petclinic
witnis bench --suite ground-truth
# or:
python -c "from pathlib import Path; from witnis.core.ground_truth import evaluate_case, load_label; ..."
```
