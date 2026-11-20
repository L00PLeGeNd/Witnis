# Demo: modify token refresh

Users do not stay for MCP tool catalogs. They stay for **engineering outcomes**.

## Task

Change token refresh so **expired refresh tokens are rejected**, without breaking login or the auth filter.

## Walkthrough (what you should see)

```bash
pip install -e .
witnis scene
witnis browser-demo    # same story as HTML in the browser
```

1. **Task** — stated in plain language  
2. **Context** — definitions + callers (controller / filter / tests)  
3. **Impact** — direct edges + related tests  
4. **Guidance** — edit from evidence, not a repo-wide guess  
5. **Verification** — plan steps; optional gated execute

Optional proof:

```bash
WITNIS_ALLOW_VERIFY=1 witnis scene --execute
```

## Why not “just let the agent read the repo”?

| Bare agent | Witnis scene |
|---|---|
| Opens files until context fills | Returns typed callers + impact edges |
| Grep-like string hits | Symbol hits with file:line kinds |
| “Tests passed” as chat claim | Gated verify with explicit state + isolation |

Fixture: [`fixtures/auth_refresh/`](../fixtures/auth_refresh/)
