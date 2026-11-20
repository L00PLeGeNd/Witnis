# Experiments

`witnis experiment` measures **analysis completeness** (grep vs Witnis). It is not LLM Agent A/B and not dual-human labeling.

| Artifact | What |
|---|---|
| [`../../benchmarks/experiments/ab_analysis_pack.json`](../../benchmarks/experiments/ab_analysis_pack.json) | Pack: fixtures + optional PetClinic `Person` |
| [`results/petclinic-person-impact.json`](results/petclinic-person-impact.json) | Pin snapshot: grep 0.0 / impact 1.0 on controllers |
| [`../benchmarks/petclinic-person-grep-vs-impact.md`](../benchmarks/petclinic-person-grep-vs-impact.md) | How to reproduce |

```bash
# optional: clone pin under benchmarks/ground-truth/corpora/checkouts/spring-petclinic
witnis experiment
```
