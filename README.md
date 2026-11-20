# Witnis

Public name: **witnis-dev**. This project is not [Witnis AB](https://www.witnis.se).

Witnis indexes a repo and answers two questions agents get wrong: what else did this change touch, and did the tests actually run.

Default verify is blocked. Nothing executes until you set `WITNIS_ALLOW_VERIFY=1` and pass `--execute`. A PR comment that says `automation_verified` means commands ran, not that a human signed off.

<img src="./docs/assets/caught-lying.svg" alt="Agent says tests passed; Witnis shows executed 0, blocked; after authorize, pytest ran." width="960"/>

## GitHub Action

Needs a checkout with history (`fetch-depth: 0`). The rest is the Action:

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- uses: L00PLeGeNd/Witnis/.github/actions/pr-gate@master
```

On a pull request it leaves a sticky comment: blast radius, whether verify was blocked or ran, exit codes. CI default is blocked / 0 commands.

## MCP / CLI

Four tools on the default MCP surface: `index`, `look`, `impact`, `verify`. Everything else is behind `WITNIS_MCP_EXPERIMENTAL=1`.

```bash
uvx --from git+https://github.com/L00PLeGeNd/Witnis.git witnis loop-init
```

That indexes the tree, writes a Cursor/Claude MCP snippet, and a stdio policy (Harnis sits in front of the server; it is not a second product). `WITNIS_DB` defaults to `.witnis/index.sqlite` in the workspace.

```json
{
  "mcpServers": {
    "witnis": {
      "command": "npx",
      "args": [
        "-y", "harnis", "mcp", "--preset", "coding-agent", "--",
        "uvx", "--from", "git+https://github.com/L00PLeGeNd/Witnis.git",
        "witnis", "mcp"
      ]
    }
  }
}
```

Do not tell anyone tests passed unless `verify` returned `automation_verified=true` after an authorized execute.

Not on PyPI yet. Do not `pip install witnis` expecting this repo.

## Impact

`git grep -lw Person` on spring-petclinic misses the controllers. `witnis impact Person` follows `Owner extends Person` into `OwnerController` / `PetController` / `VisitController`.

<img src="./docs/assets/blast-radius.svg" alt="Person typed through Owner into the PetClinic controllers" width="960"/>

The labelled PetClinic set (18 items, maintainer-adjudicated, not dual-human) is in [`docs/benchmarks/petclinic-human-v2.md`](docs/benchmarks/petclinic-human-v2.md). Isolation and authorize-vs-sandbox: [`SECURITY.md`](SECURITY.md). Envelope shape: [`docs/contracts-v1.md`](docs/contracts-v1.md).

CLI of note: `look`, `impact`, `verify`, `pr-gate`. Apache-2.0.
