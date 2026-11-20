# PetClinic: `git grep Person` vs Witnis impact

Corpus: [spring-petclinic](https://github.com/spring-projects/spring-petclinic) @ `500158f732419217507c7656904b8e6aa1bcc0d6`  
Reproduce: clone per [`../benchmarks/ground-truth/blind-pack/CLONE.md`](../../benchmarks/ground-truth/blind-pack/CLONE.md), then the public CLI (not only the experiment harness):

```bash
witnis index benchmarks/ground-truth/corpora/checkouts/spring-petclinic --db .witnis/petclinic.sqlite --full
witnis impact Person --db .witnis/petclinic.sqlite --plain
witnis look Person --db .witnis/petclinic.sqlite
```

`impact --plain` and `look` must name `OwnerController`, `PetController`, `VisitController`. JSON default of `impact` includes the same `transitive` edges. A PR-gate comment whose hunks include `Person` must list those controllers under **transitive edges**, even if the 6-line blast hop is full of Direct `calls`. Java hunk overlap uses class span (method-body edits still attach to `Person`); `_symbols_overlapping_hunks`, `explain_change` / `change-impact`, and `compare_revisions` / `compare_worktree` parse `.java` blobs. `witnis scene` impact sample includes transitive typed users (not direct-only). Pack task: `petclinic-person-impact` in [`ab_analysis_pack.json`](../../benchmarks/experiments/ab_analysis_pack.json).

This is **analysis completeness**, not LLM Agent A/B. Dual-human GT is still open.

## What string search sees

`git grep -lw Person -- '*.java'` on that pin (5 files):

- `src/main/java/org/springframework/samples/petclinic/model/Person.java`
- `src/main/java/org/springframework/samples/petclinic/owner/Owner.java`
- `src/main/java/org/springframework/samples/petclinic/vet/Vet.java`
- `src/main/java/org/springframework/samples/petclinic/PetClinicRuntimeHints.java`
- `src/test/java/org/springframework/samples/petclinic/model/ValidatorTests.java`

None of `OwnerController`, `PetController`, `VisitController` contain the token `Person`. They talk about `Owner`. A grep/native-agent first pass that stops at name hits never names those controllers.

Arm A caller recall on those three names: **0.0**.

## What impact adds

`witnis impact Person` / `analyze_impact(..., target="Person")` on the same pin:

- Direct: `Owner` / `Vet` inherit `Person`; RuntimeHints import; validator tests.
- Transitive (one-hop `uses_type` through subclass `Owner`): `OwnerController`, `PetController`, `VisitController`.

Arm B caller recall on those three names: **1.0**.

## What this does not prove

- Not that an LLM agent with Witnis wins task success or token cost (protocol still open).
- Not dual-human labels.
- Not AOP / `@Primary` / full classpath Java depth.
