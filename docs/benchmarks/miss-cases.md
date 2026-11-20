# Public bench vs known misses

Green public acceptance (`witnis bench --suite public`) is **fixture smoke**. Known product misses live in [`FAILURE_CASES.md`](../FAILURE_CASES.md). This page ties the two so a green CI score cannot be read as “no misses.”

## What public green means

| True | False |
| --- | --- |
| Listed acceptance tasks passed on repo fixtures | Full-repo semantic leadership |
| Envelope / gate / multi-lang smoke contracts hold | Indirect typed-use recall is solved |
| Safe to merge Core regressions | PetClinic Indirect R > 0 |

Scores: [`PUBLIC.md`](PUBLIC.md) · CI HTML: [`ci-report.md`](ci-report.md) · GT: [`petclinic-human-v2.md`](petclinic-human-v2.md)

## Miss map (stable F ids)

| Id | Short | Public suite? | Where it shows |
| --- | --- | --- | --- |
| F1 | Typed-use Indirect FN | mitigated (Java `uses_type`) | PetClinic human-v2 · was FN; now TP on pin |
| F2 | Auto label ≠ human GT | not covered | `spring_petclinic_auto.json` noise |
| F3 | Self-call / tautology Direct | not covered | Auto OwnerController noise |
| F4–F9 | See gallery | mostly out of scope | [`FAILURE_CASES.md`](../FAILURE_CASES.md) |
| F10 | Public score ≠ accuracy | **meta** | This page + README disclaimer |

Public tasks must stay green. New semantic claims need a GT label or an F-row — not a silent public-task tweak.

## Reproduce the honesty path

```bash
python -m witnis bench --suite public
# with PetClinic checkout:
python -m witnis bench --suite ground-truth
# read F1 after Indirect FN
```

## Related

- [`extensions.md`](../extensions.md) — new tools must link misses  
- [`rust-full-binary.md`](../rust-full-binary.md) — Rust ports inherit the same bar  
