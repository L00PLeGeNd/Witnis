# Witnis CLI cheatsheet

Short path first. Long forms still work.

## First run

```bash
pip install -e ".[dev,lsp]"
witnis demo
witnis look login
```

## Everyday

```
index a repo     witnis index .
witness card     witnis look <symbol>
plan checks      witnis plan <symbol>
run checks       WITNIS_ALLOW_VERIFY=1 witnis verify <symbol> --execute
studio           witnis studio <symbol> --open
related tests    witnis tests <symbol>
baselines        witnis baselines fixtures/mini_py
public bench     witnis bench --suite public
```

## MCP (any compatible host)

```bash
witnis index /path/to/repo
# point WITNIS_DB at /path/to/repo/.witnis/index.sqlite
witnis mcp
```

Sample config: [`examples/mcp.example.json`](../examples/mcp.example.json)

## Aliases

```
plan        → plan-verify
tests       → related-tests
baselines   → compare-baselines
look        → search + trace + impact + tests + plan
demo        → index sample fixture + look
```
