# Corpus pin: spring-petclinic (Benchmark V1)

**Status:** checked out locally (gitignored under `corpora/checkouts/`)  
**License:** Apache-2.0  
**Upstream:** https://github.com/spring-projects/spring-petclinic  

| Field | Value |
| --- | --- |
| SHA | `500158f732419217507c7656904b8e6aa1bcc0d6` |
| Local path | `benchmarks/ground-truth/corpora/checkouts/spring-petclinic` |
| Labels | `labels/spring_petclinic_human.json` (human-v2 adjudicated) · `labels/spring_petclinic_auto.json` (auto bootstrap) |

```bash
# refresh
git -C benchmarks/ground-truth/corpora/checkouts/spring-petclinic fetch
git -C benchmarks/ground-truth/corpora/checkouts/spring-petclinic rev-parse HEAD
python scripts/bootstrap_petclinic_gt.py
```
