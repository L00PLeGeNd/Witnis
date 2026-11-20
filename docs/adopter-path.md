# Default adopter path

**Recommended daily path for teams adopting Witnis** (Stage-2 Mid):  
keep a **fresh incremental index**, ship **PR evidence**, export a **bundle/report** when you need a proof pack.

This is the path we want new adopters to learn first — not every CLI command.

```text
once     →  loop-init  (+ Harnis wrap)  →  merge MCP config
daily    →  refresh / watch            →  look / impact
every PR →  pr-gate Action             →  sticky comment
handoff  →  export-bundle / report     →  share evidence
proof    →  authorize verify only when intentional
```

---

## 1. Once per repo

```bash
uvx witnis loop-init
# merge .witnis/mcp.loop.json into Cursor / Claude
```

Copy-paste seed: [`examples/witnis-harnis-starter/`](../examples/witnis-harnis-starter/).  
Loop semantics: [`trusted-agent-loop.md`](trusted-agent-loop.md).

`index` is **incremental by default**. Use `witnis index . --full` only after corruption or major tree moves.

---

## 2. Keep the index fresh (incremental)

| Command | When |
| --- | --- |
| `witnis refresh` | After a batch of local edits / pull |
| `witnis watch --interval 20` | Long agent sessions (periodic incremental refresh) |
| `witnis refresh-evidence` | Mark persisted evidence stale when watched files changed |
| Action / `pr-gate` | Re-indexes the PR head unless `--no-reindex` |

**STALE:** if `indexed_revision` lags HEAD, envelopes warn — refresh before trusting impact. See [FAILURE_CASES F6](FAILURE_CASES.md#f6--index-stale-vs-live-head).

Agents on MCP should call `refresh_index` (or you run `witnis refresh`) before large edit plans.

---

## 3. Every PR (distribution default)

Prefer **three-dot PR range** over tip-commit `change-impact`:

```bash
witnis pr-gate --base origin/main --head HEAD --format markdown -o pr-gate.md
```

Or the composite Action (already in the starter workflow):  
[`.github/actions/pr-gate`](../.github/actions/pr-gate) · starter: [`examples/witnis-harnis-starter/.github/workflows/witnis-pr-gate.yml`](../examples/witnis-harnis-starter/.github/workflows/witnis-pr-gate.yml)

Default PR runs **do not** execute verify.

---

## 4. Export when you need a proof pack

| Command | Output |
| --- | --- |
| `witnis export-bundle --target <symbol> -o bundle.json` | Agent-facing JSON evidence pack |
| `witnis report --target <symbol> -o report.md` | Markdown derived from the bundle |
| `witnis report --target <symbol> --html-out report.html` | HTML view |
| `witnis studio <symbol> --open` | Local Studio dashboard |

Use exports for review packets, incident notes, or attaching context next to a PR — not as a substitute for `pr-gate` on GitHub.

---

## 5. Verify only when intentional

```bash
witnis plan <symbol>                                    # blocked plan
WITNIS_ALLOW_VERIFY=1 witnis verify <symbol> --execute  # automation only
```

Authorize ≠ OS sandbox. Pair MCP with Harnis seatbelt. Honesty: [FAILURE_CASES F7–F8](FAILURE_CASES.md).

---

## What not to lead with

- Full tool catalogs / MCP tool dumps  
- Single-commit `change-impact` as the PR story ([F5](FAILURE_CASES.md#f5--change-impact--full-pr))  
- Java deep-dive claims (honest shallow)  
- “Verified” as human sign-off  

Cheatsheet: [`cli-cheatsheet.md`](cli-cheatsheet.md) · Agent playbook: [`examples/agent-playbook.md`](../examples/agent-playbook.md)
