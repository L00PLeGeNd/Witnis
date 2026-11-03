# Witnis agent playbook (local)

Witnis is evidence infrastructure: index → trace → impact → verify. Prefer facts from Core tools over model guesses.

## Bootstrap

```bash
pip install -e ".[dev]"
python -m witnis index /path/to/repo
python -m witnis status
python -m witnis capabilities
```

MCP: point `WITNIS_DB` at `.witnis/index.sqlite` (see `examples/mcp.cursor.example.json`).

## Typical loops

1. **Understand a symbol**  
   `trace` → `explain` → `impact` → `related-tests` → `graph`

2. **Review a commit**  
   `explain-change HEAD` → `change-impact HEAD` → `plan-verify --revision HEAD`

3. **Review dirty worktree**  
   `compare-worktree` → `refresh` → `plan-verify --target <symbol>`

4. **Ship a proof pack**  
   `export-bundle --target X` or `report --target X --html-out out.html`

5. **Authorize checks** (explicit only)  
   `WITNIS_ALLOW_VERIFY=1 python -m witnis verify --execute --target X`

## Safety defaults

- Verification is blocked without `--execute` **and** `WITNIS_ALLOW_VERIFY=1`
- Allowlisted commands only: pytest / compileall (+ in-process syntax/graph)
- Paths sandboxed to the indexed repo root; stdout redacted for secret-like assignments
- `scan-secrets` is heuristic and redacts previews

## Evidence statuses

`observed` · `derived` · `verified` · `uncertain` · `failed` — treat `verified` as post-check only.
