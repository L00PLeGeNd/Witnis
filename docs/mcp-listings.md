# MCP directory listings

Stage-2 distribution kit: **repo payloads are ready**; **form submission is manual** after push.

Canonical copy: [`docs/listings/identity.json`](listings/identity.json)  
Short description (≤100 chars):  
`Evidence envelopes for agent change: blast-radius, PR gate, gated verify.`

## Payloads in this repo

| File | Directory / use |
| --- | --- |
| [`glama.json`](../glama.json) | [Glama](https://glama.ai/mcp/servers) claim (`maintainers`) |
| [`server.json`](../server.json) | Official [MCP Registry](https://registry.modelcontextprotocol.io) (`mcp-publisher`) |
| [`.mcp.json`](../.mcp.json) | [cursor.directory](https://cursor.directory) auto-detect |
| [`Dockerfile.mcp`](../Dockerfile.mcp) | Reference stdio image / Glama Admin paste source |

Companion seatbelt: Harnis already has `glama.json` in its repo.

## Submission checklist (do after push)

### 1. Glama

1. Ensure `glama.json` is on the default branch.  
2. [Add MCP Server](https://glama.ai/mcp/servers) → paste `https://github.com/L00PLeGeNd/Witnis`.  
3. Claim ownership (maintainer must match `L00PLeGeNd`).  
4. Admin → Listing: paste `description_400` from `identity.json`.  
5. Admin → Dockerfile: use `Dockerfile.mcp` as the command reference (`witnis mcp`, `WITNIS_DB`).

### 2. Official MCP Registry

```bash
# after PyPI has the matching version
npm install -g mcp-publisher   # or current install docs
mcp-publisher login
mcp-publisher publish          # reads server.json
```

Namespace `io.github.L00PLeGeNd/witnis` requires GitHub auth for that owner.

### 3. mcp.so

Free form: https://mcp.so/submit — repo URL + name **Witnis** + short description.  
Or PR one line to their index (if still accepted):

```text
- [Witnis](https://github.com/L00PLeGeNd/Witnis) — Evidence envelopes for agent change: blast-radius, PR gate, gated verify.
```

### 4. cursor.directory

Submit the GitHub repo via the website form. Detector expects root `.mcp.json`.

### 5. Smithery

**Skip for now** — Witnis is **stdio-local**, not a public Streamable-HTTP endpoint. Smithery proxy path is deferred / sunset-sensitive.

## Honesty on listing pages

- Authorize ≠ OS sandbox; Harnis ≠ jail.  
- Public bench score ≠ corpus leadership.  
- Link [`FAILURE_CASES.md`](FAILURE_CASES.md) and [`trusted-agent-loop.md`](trusted-agent-loop.md) from the Glama/README blurb when possible.
