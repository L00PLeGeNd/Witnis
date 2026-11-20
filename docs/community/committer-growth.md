# Committer growth

How we grow maintainers without lowering the honesty bar.

## Path

1. **Good first issue** — seeds in [`gfi-seeds/`](gfi-seeds/) · pipeline [`good-first-issue-pipeline.md`](good-first-issue-pipeline.md).  
2. **Docs / fixtures / miss links** — safest first merges; see [`extensions.md`](../extensions.md).  
3. **Core with fixtures** — envelopes + benches green; no silent contract breaks.  
4. **Reviewer** — consistent review on GFI + small Core PRs.  
5. **Committer** — sustained reviews + at least one owned area (bench, Rust core, MCP docs, …).

## Review expectations

| Expect | Detail |
| --- | --- |
| Response | Aim to triage newcomer PRs within a few days when possible |
| Bar | Public bench green; contracts stable unless the issue says otherwise |
| Honesty | Reject PRs that delete expected GT misses or inflate P/R |
| Scope | Prefer one concern per PR ([`CONTRIBUTING.md`](../../CONTRIBUTING.md)) |

## What we will not trade for headcount

- Fake dual-human GT  
- “Verified” without automation caveats  
- Harnis-as-sandbox marketing  
- Merging Agent A/B execution before baseline readiness  

## Maintainer checklist (monthly)

- [ ] At least one open GFI labeled and linked from seeds  
- [ ] `miss-cases.md` / FAILURE_CASES still linked from README Status / bench summary  
- [ ] Thank / credit first-time contributors in release notes when shipping  

## Related

- [`CONTRIBUTING.md`](../../CONTRIBUTING.md)  
- [`ADOPTERS.md`](../../ADOPTERS.md) · [`SHOWCASE.md`](../SHOWCASE.md)  
