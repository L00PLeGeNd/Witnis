# Witnis agent playbook (local)

Prefer Core facts over model guesses.

## Bootstrap (default adopter path)

Canonical guide: [`docs/adopter-path.md`](../docs/adopter-path.md).

```bash
uvx --from git+https://github.com/L00PLeGeNd/Witnis.git witnis loop-init
# merge .witnis/mcp.loop.json into the MCP client
witnis look <symbol>
```

Short demos: `witnis scene` / `witnis browser-demo` / `witnis demo`.

Prefer `look` / impact / `pr-gate` / gated verify over dumping the whole MCP tool list.

## Typical loops

1. **Keep index fresh** — `witnis refresh` or `witnis watch` (incremental)

2. **Understand a symbol** — `witnis look <symbol>`  
   (or `trace` / `impact` / `tests` / `graph` when you need one slice)

3. **Before editing (Trusted Agent Loop)**  
   `witnis look <symbol>` / `witnis impact <symbol>` → edit from evidence → `witnis plan <symbol>`

4. **Review a PR range (default distribution path)**  
   `witnis pr-gate --base origin/main --head HEAD --format markdown`

5. **Review a single commit**  
   `witnis explain-change HEAD` → `witnis change-impact HEAD` → `witnis plan --revision HEAD`

6. **Dirty worktree**  
   `witnis compare-worktree` → `witnis refresh` → `witnis plan <symbol>`

7. **Proof pack (export)**  
   `witnis export-bundle --target X -o bundle.json` or `witnis report --target X --html-out out.html`

8. **Authorize checks** (explicit only)  
   `WITNIS_ALLOW_VERIFY=1 witnis verify X --execute`  
   Harnis wrap: `witnis loop-init` · [`docs/trusted-agent-loop.md`](../docs/trusted-agent-loop.md)

## Short aliases

| Short | Full |
|---|---|
| `look` | search + trace + impact + tests + plan card |
| `plan` | `plan-verify` |
| `tests` | `related-tests` |
| `baselines` | `compare-baselines` |

## Safety defaults

- Verify stays blocked without `--execute` **and** `WITNIS_ALLOW_VERIFY=1`
- Allowlisted runners only (pytest / compileall + in-process checks)
- Paths sandboxed to the indexed root; secret-like values redacted
