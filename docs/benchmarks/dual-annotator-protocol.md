# Dual-annotator protocol (Benchmark V1+)

Used for PetClinic human GT and any future corpus that claims **adjudicated** labels.

## Roles

| Role | Job |
| --- | --- |
| Annotator A | First pass: fill `expect` from pinned sources using [`LABELING_SHEET.md`](../../benchmarks/ground-truth/LABELING_SHEET.md) |
| Annotator B | Second pass: **blind** — only [`blind-pack/`](../../benchmarks/ground-truth/blind-pack/); mark **Keep / Drop / Edit / Unsure** |
| Adjudicator | Resolve disagreements; record reason; update label JSON |

## Rules

1. Same pin SHA for A and B.  
2. Direct / Indirect definitions stay fixed — see [`SCOPE.md`](../../benchmarks/ground-truth/SCOPE.md).  
3. Disagreement → keep the **stricter** recall-facing label if the edge is real in source (do not delete hard Indirect just to greenwash).  
4. Solo maintainer “B pass” must be labeled `human-v2-adjudication` (second-pass), **not** claimed as a second person.  
5. AI-assisted or non-blind reviews are welcome as quality feedback; they do **not** upgrade `label_mode` to `human_dual`.  
6. True dual-human (two people, blind pack) upgrades `label_mode` to `human_dual`.

## Artifact layout

```
benchmarks/ground-truth/
  labels/spring_petclinic_human.json     # canonical expects after adjudication
  adjudication/petclinic-human-v2.md     # A/B table + resolutions
docs/benchmarks/
  petclinic-human-v2.md                  # published scores + honesty
  dual-annotator-protocol.md             # this file
```
