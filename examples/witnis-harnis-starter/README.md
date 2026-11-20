# Witnis starter (seatbelt included)

One name: **Witnis** (search **witnis-dev**). Copy this folder into your app repo, or skip the copy and run:

```bash
uvx --from git+https://github.com/L00PLeGeNd/Witnis.git witnis loop-init
```

Merge `.witnis/mcp.loop.json` into Cursor / Claude. Drop the Action:

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- uses: L00PLeGeNd/Witnis/.github/actions/pr-gate@v1
```

Do not tell anyone tests passed unless the PR comment says `automation_verified` after executed commands.

## What this folder is

| Path | Role |
| --- | --- |
| `.harnis/policy.json` | Seatbelt budgets (stdio MCP only) |
| `.witnis/mcp.loop.example.json` | Hand-merge if you skip `loop-init` |
| `.github/workflows/witnis-pr-gate.yml` | Sticky PR comment + check |

Verify stays blocked until `WITNIS_ALLOW_VERIFY=1` + `--execute`.
