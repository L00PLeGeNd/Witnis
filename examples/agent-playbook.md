# Witnis agent playbook (local)

Prefer Core facts over model guesses.

## Bootstrap

```bash
pip install -e ".[dev,lsp]"
witnis index /path/to/repo
witnis look login
```

Or the shortest first run: `witnis demo`

MCP: set `WITNIS_DB` to `.witnis/index.sqlite` (see `examples/mcp.example.json`). Any MCP-compatible host works.

## Typical loops

1. **Understand a symbol** — `witnis look <symbol>`  
   (or `trace` / `impact` / `tests` / `graph` when you need one slice)

2. **Review a commit**  
   `witnis explain-change HEAD` → `witnis change-impact HEAD` → `witnis plan --revision HEAD`

3. **Dirty worktree**  
   `witnis compare-worktree` → `witnis refresh` → `witnis plan <symbol>`

4. **Proof pack**  
   `witnis export-bundle --target X` or `witnis report X --html-out out.html`

5. **Authorize checks** (explicit only)  
   `WITNIS_ALLOW_VERIFY=1 witnis verify X --execute`

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
