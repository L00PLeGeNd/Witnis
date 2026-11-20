# Public bench vs known misses

Green public acceptance (`witnis bench --suite public`) is **fixture smoke**. Known product misses live in [`FAILURE_CASES.md`](../FAILURE_CASES.md).

## What public green means

| True | False |
| --- | --- |
| Listed acceptance tasks passed on repo fixtures | Full-repo semantic leadership |
| Envelope / gate / multi-lang smoke contracts hold | Indirect typed-use is fully solved |
| Safe to merge Core regressions | Dual-human PetClinic labels exist |

GT: [`petclinic-human-v2.md`](petclinic-human-v2.md) (not dual-human).  
Grep vs impact: [`petclinic-person-grep-vs-impact.md`](petclinic-person-grep-vs-impact.md).

## Miss map (stable F ids)

| Id | Short | Notes |
| --- | --- | --- |
| F1 | Typed-use Indirect FN | mitigated on PetClinic pin via Java `uses_type` |
| F2–F9 | See gallery | [`FAILURE_CASES.md`](../FAILURE_CASES.md) |
| F10 | Public score ≠ accuracy | this page + README disclaimer |

```bash
python -m witnis bench --suite public
# with PetClinic checkout:
python -m witnis bench --suite ground-truth
```
