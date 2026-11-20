# Experiments

**Status:** grep vs Witnis **analysis pack** is runnable (`witnis experiment`), including PetClinic `Person` when the gitignored checkout exists. **LLM Agent A/B** (task success / tokens) stays paused until independent humans fill the sheet.

| Artifact | What it is | Command / use |
|---|---|---|
| [`EXPERIMENT_REPORT_FILLME.md`](EXPERIMENT_REPORT_FILLME.md) | Fill-in report + ops tutorial (resume later) | when LLM A/B restarts |
| [`results/ab-analysis-v1.json`](results/ab-analysis-v1.json) | Fixture-level grep vs Witnis completeness | `witnis experiment` |
| [`results/petclinic-person-impact.json`](results/petclinic-person-impact.json) | Pin snapshot: grep 0.0 / impact 1.0 | clone pin, then `witnis experiment` |
| [`../benchmarks/petclinic-person-grep-vs-impact.md`](../benchmarks/petclinic-person-grep-vs-impact.md) | Real PetClinic pin: grep 0 vs impact 1.0 on controllers | clone pin, then `witnis experiment` |
| [`agent-ab-sheet.md`](agent-ab-sheet.md) | Agent task A/B sheet | paused (LLM) |
| [`agent-effect-protocol.md`](agent-effect-protocol.md) | Metric definitions | reference |
| [`../demo-auth-refresh.md`](../demo-auth-refresh.md) | Product story demo | `witnis scene` |

No agent-leadership claims until real-corpus experiments pass the plan’s go/no-go gates.
