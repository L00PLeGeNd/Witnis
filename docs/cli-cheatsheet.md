# Witnis CLI cheatsheet

Short path first. Long forms still work.

## First run

```bash
pip install -e ".[dev,lsp]"
witnis demo
witnis look login
```

## Everyday (default adopter path)

Full narrative: [`adopter-path.md`](adopter-path.md).

| Goal | Command |
|---|---|
| Project homepage (CSS motion) | `witnis home` |
| Bootstrap + Harnis wrap | `witnis loop-init` |
| Index a repo (incremental) | `witnis index .` |
| Refresh after edits | `witnis refresh` / `witnis watch` |
| Witness card | `witnis look <symbol>` |
| PR evidence gate | `witnis pr-gate --base origin/main --head HEAD` |
| Export proof pack | `witnis export-bundle --target X -o bundle.json` |
| Markdown / HTML report | `witnis report --target X --html-out out.html` |
| Plan checks | `witnis plan <symbol>` |
| Run checks | `WITNIS_ALLOW_VERIFY=1 witnis verify <symbol> --execute` |
| Studio | `witnis studio <symbol> --open` |
| Related tests | `witnis tests <symbol>` |
| Public bench + HTML | `witnis bench --suite public --report out.html` |

## MCP (any compatible host)

```bash
witnis index /path/to/repo
# point WITNIS_DB at /path/to/repo/.witnis/index.sqlite
witnis mcp
```

Sample config: [`examples/mcp.example.json`](../examples/mcp.example.json)

## Aliases

| Short | Full |
|---|---|
| `plan` | `plan-verify` |
| `tests` | `related-tests` |
| `baselines` | `compare-baselines` |
| `look` | search + trace + impact + tests + plan |
| `demo` | index sample fixture + `look` |
