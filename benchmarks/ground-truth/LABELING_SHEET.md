# Ground-truth labeling sheet (Benchmark V1)

Aligns with `docs/strategy/architecture-audit-2026-11-04.md` §9.

## Classes

```
Class       Include when…                                                                    Exclude when…
----------  -------------------------------------------------------------------------------  -----------------------------------------------
Direct      Caller / inject site / implementor / override must change or retest if symbol    Same name elsewhere with no edge
            changes
Indirect    Documented 2+ hop or framework-mediated path                                     Speculative “maybe related”
Test link   Test fails or must run if symbol changes                                         Unrelated test file that only shares a string
Non-impact  String/grep hit only                                                             —
```

## Process

1. Pin corpus SHA (`corpora/*.pin.md`).  
2. Copy `labels/_TEMPLATE_case.json` → `labels/<corpus>-<id>.json`.  
3. Annotator A fills expect edges/symbols.  
4. Hard cases: Annotator B independent; resolve disagreements in notes.  
5. Run `witnis bench --suite ground-truth` only for **vendored** labels; external corpora need a local checkout path override (future runner flag).

## Scoreboard

```
Corpus @ SHA                     N cases   Direct P  Direct R  Notes
-------------------------------  --------  --------  --------  ----------------------------------------------------------------------------------------------
semantic_java_di @ vendored      4 tasks   1.0*      1.0*      fixture
semantic_py_di @ vendored        2 tasks   1.0*      1.0*      fixture
spring-petclinic @ 500158f7      30 tasks  1.0*      1.0*      source_confirmed_auto via scripts/bootstrap_petclinic_gt.py — not dual-human;
                                                               re-run `witnis bench --suite ground-truth` locally with checkout
```

\* Measured against the same Witnis index that proposed source-confirmed edges. Treat as regression harness + bootstrap, **not** independent human GT leadership claims.
