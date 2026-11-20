# Witnis agent playbook (local)

Prefer Core facts over model guesses.

## Bootstrap

```bash
uvx witnis loop-init
# merge .witnis/mcp.loop.json into the MCP client
witnis look <symbol>
```

Short demos: `witnis scene` / `witnis browser-demo` / `witnis demo`.

Prefer `look` / impact / `pr-gate` / gated verify over dumping the whole MCP tool list.

## Typical loops

1. **Keep index fresh** — `witnis refresh` or `witnis watch` (incremental)

2. **Understand a symbol** — `witnis look <symbol>`  
   (or `trace` / `impact` / `tests` / `graph` when you need one slice)

3. **Before editing**  
   `witnis look <symbol>` / `witnis impact <symbol>` → edit from evidence → `witnis plan <symbol>`

4. **Review a PR range**  
   `witnis pr-gate --base origin/main --head HEAD --format markdown`

5. **Review a single commit**  
   `witnis explain-change HEAD` → `witnis change-impact HEAD` → `witnis plan --revision HEAD`

6. **Dirty worktree**  
   `witnis compare-worktree` → `witnis refresh` → `witnis plan <symbol>`

7. **Proof pack**  
   `witnis export-bundle --target X -o bundle.json` or `witnis report --target X --html-out out.html`

## Rules of thumb

- `automation_verified` means commands ran under the gate — not a human review.
- Verify stays blocked until `WITNIS_ALLOW_VERIFY=1` and `--execute`.
- On Java/Spring, string search is not blast radius; use `impact` (see PetClinic Person notes under `docs/benchmarks/`).

More: [`docs/trusted-agent-loop.md`](../docs/trusted-agent-loop.md) · [`docs/cli-cheatsheet.md`](../docs/cli-cheatsheet.md).
