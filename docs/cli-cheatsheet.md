# Witnis CLI cheatsheet

Short path first. Long forms still work.

## First run

```bash
pip install -e ".[dev,lsp]"
witnis demo
witnis look login
```

## Everyday

| Goal | Command |
|---|---|
| Index a repo | `witnis index .` |
| Witness card | `witnis look <symbol>` |
| Plan checks | `witnis plan <symbol>` |
| Run checks | `WITNIS_ALLOW_VERIFY=1 witnis verify <symbol> --execute` |
| Studio | `witnis studio <symbol> --open` |
| Related tests | `witnis tests <symbol>` |
| Baselines | `witnis baselines fixtures/mini_py` |
| Public bench | `witnis bench --suite public` |

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
