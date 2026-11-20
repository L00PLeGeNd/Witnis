# Good-first-issue pipeline

How maintainers keep a steady stream of approachable issues without diluting Core contracts.

## Labels (create once on GitHub)

| Label | Color hint | Meaning |
| --- | --- | --- |
| `good first issue` | `#7057ff` | New contributor can finish in ~1 sitting |
| `help wanted` | `#008672` | Clear problem; needs a taker |
| `docs` | `#0075ca` | Docs / examples only |
| `loop` | `#0c5c48` | Trusted Agent Loop / Harnis wrap |
| `benchmark` | `#fbca04` | Bench / GT / FAILURE_CASES |
| `question` | `#d876e3` | Support (prefer Discussions) |

## Intake → label → ship

```text
Idea / bug / doc gap
  → write issue with: goal, non-goals, files to touch, acceptance commands
  → if ≤1 evening + no contract break → good first issue
  → else help wanted or keep unlabeled
  → PR cites acceptance commands from CONTRIBUTING
```

## What qualifies as good first issue

**Yes**

- Docs typo / cheatsheet row / showcase row  
- New example MCP JSON for a known client  
- FAILURE_CASES cross-link  
- Tiny fixture assertion under existing tests  
- Translate a short UI string already wired in Studio i18n  

**No** (keep off `good first issue`)

- Envelope / MCP contract changes  
- Java Spring deep semantics  
- Verify isolate / security model redesign  
- Anything needing PetClinic dual-annotator judgment without a template  

## Seed drafts (paste into GitHub after push)

Ready-to-open bodies: [`gfi-seeds/`](gfi-seeds/).

## Cadence

- Aim for **3–5** open `good first issue` at a time.  
- When one closes, open the next seed or promote a `help wanted`.  
- Point newcomers at [`adopter-path.md`](../adopter-path.md) + [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
