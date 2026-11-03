# Witnis agent playbook (local)

Prefer Core facts over model guesses.

## Bootstrap

```bash
pip install -e .
witnis scene                 # show the product story before tool names
witnis index /path/to/repo
witnis look refresh_token    # or login / your symbol
```

Shortest first runs: `witnis scene` (auth narrative) or `witnis demo`.

MCP (Claude Code, Codex, and other MCP hosts): set `WITNIS_DB` to `.witnis/index.sqlite` (see `examples/mcp.example.json`). Prefer `look` / impact / gated verify over dumping the whole tool list at the user.

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
