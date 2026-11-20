# CI bench report page

Stage-2 deliverable: every CI Python job writes **HTML report pages** and a **GitHub Actions job summary**.

## Local

```bash
witnis bench --suite public --report .witnis/bench-reports/public.html
witnis bench --suite ground-truth --report .witnis/bench-reports/ground-truth.html
# open the HTML in a browser
```

## CI

Workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)

| Output | Where |
| --- | --- |
| Job summary table | Actions run → job summary (`--github-summary`) |
| HTML pages | Artifact `witnis-bench-reports` (`public.html`, `ground-truth.html`) |

## Honesty

These pages score the **acceptance / fixture** suites (and optional ground-truth labels when checkouts exist).  
They are **not** a claim of full-repo semantic leadership. See [`FAILURE_CASES.md`](../FAILURE_CASES.md) and [`petclinic-human-v2.md`](petclinic-human-v2.md).
