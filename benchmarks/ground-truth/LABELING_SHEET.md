# Ground-truth labeling sheet (Benchmark V1)

## Classes

| Class | Include when… | Exclude when… |
| --- | --- | --- |
| Direct | Caller / inject site / implementor / override must change or retest if symbol changes | Same name elsewhere with no edge |
| Indirect | Documented 2+ hop or framework-mediated path | Speculative “maybe related” |
| Test link | Test fails or must run if symbol changes | Unrelated test file that only shares a string |
| Non-impact | String/grep hit only | — |

## Process

1. Pin corpus SHA (`corpora/*.pin.md`).  
2. Read [`SCOPE.md`](SCOPE.md) (production vs test, generics, etc.).  
3. Copy `labels/_TEMPLATE_case.json` → `labels/<corpus>-<id>.json`.  
4. Annotator A fills expect edges/symbols / Direct+Indirect impact sets.  
5. Annotator B: send **[`blind-pack/`](blind-pack/) only**; vocabulary Keep/Drop/Edit/Unsure.  
6. `witnis bench --suite ground-truth` scores fixtures in CI; PetClinic needs checkout under `corpora/checkouts/` (gitignored).  
7. Metrics = expected-item recall (+ Indirect FP for unexpected main `uses_type`); not full-app precision.

## Scoreboard

| Corpus @ SHA | N cases | Direct P | Direct R | Notes |
| --- | --- | --- | --- | --- |
| semantic_java_di @ vendored | 4 tasks | 1.0* | 1.0* | fixture |
| semantic_py_di @ vendored | 2 tasks | 1.0* | 1.0* | fixture |
| spring-petclinic @ 500158f7 | 30 tasks | 1.0* | 1.0* | `spring_petclinic_auto.json` — source_confirmed_auto bootstrap, **not** human GT |
| spring-petclinic @ 500158f7 | **18 tasks** | **Direct 1.0 / 1.0** | **Indirect 1.0 / 1.0** (3 Indirect expects) | human-v2 adjudicated + FYLGls AI review archived; **not** dual-human; see SCOPE + blind-pack |

\* Auto/fixture scores measured against the same Witnis index that proposed edges — regression harness, not independent leadership claims.

## Human subset (v2 adjudicated) — decisions

A = human-v1; B = maintainer second-pass (`human-v2-adjudication`, **not a second person**). Protocol: [`docs/benchmarks/dual-annotator-protocol.md`](../../docs/benchmarks/dual-annotator-protocol.md).

| Task | Class | Decision |
| --- | --- | --- |
| OwnerController / OwnerRepository locate | — | Keep (A/B agree) |
| Owner/Pet/VisitController → OwnerRepository injects | Direct | Keep |
| VetController → VetRepository injects | Direct | Keep |
| PetTypeFormatter → PetTypeRepository injects | Direct | Keep |
| **PetController → PetTypeRepository injects** | Direct | **Added** (B gap-fill) |
| PetTypeFormatter implements Formatter | Direct | Keep |
| Owner/Vet → Person inherits | Direct | Keep |
| NamedEntity → BaseEntity inherits | Direct | Keep |
| Impact OwnerRepository → three controllers | Direct | Keep |
| Impact Person → Owner, Vet | Direct | Keep |
| Impact Person → OwnerController | Indirect | Keep — honesty / F1; do not drop to inflate R |
| Impact VetRepository → VetController | Direct | Keep |
| **Impact PetTypeRepository → Formatter + PetController** | Direct | **Added** (B gap-fill) |

### Rejected (do not promote auto → human)

| Auto id | Why |
| --- | --- |
| `auto_implements_001` (`for` → Serializable) | Parser/name noise; not a real type edge → gallery **F2** |
| Constructor self-`calls` OwnerController | Tautological / not blast-radius signal → gallery **F3** |

Product-wide honest misses: [`docs/FAILURE_CASES.md`](../../docs/FAILURE_CASES.md).

## How to refresh

```bash
python scripts/bootstrap_petclinic_gt.py   # auto only
# edit labels/spring_petclinic_human.json by hand after reading sources
witnis bench --suite ground-truth
```
