# Security model hardening checklist

Companion to root [`SECURITY.md`](../SECURITY.md). Stage-3 hardening is **policy + isolation honesty**, not a claim of audited jail.

## Threats we accept ownership for

| Threat | Current control | Still open |
| --- | --- | --- |
| Path escape on index / ingest | Root sandbox + symlink checks | Exotic junction / UNC edge cases |
| Accidental secret ingest | Filename skip + redacted previews | Content-only secrets without keyword shapes |
| Unauthorized verify | `WITNIS_ALLOW_VERIFY` + `--execute` | Operator misunderstands gate as sandbox |
| Verify side effects | Worktree/copy, scrubbed env, timeout, FS diff; optional `--profile container` (`--network none --read-only`) | cgroup / seccomp; default image has no pytest |
| Prompt injection via repo text | Documented untrusted input | Agents that ignore the warning |
| MCP tool abuse | Harnis wrap (optional seatbelt) | Harnis ≠ OS sandbox; `--no-harnis` exists |

## Loop defaults (must stay true)

1. Read-only Core by default.  
2. Verify blocked until both env gate and `--execute`.  
3. `result.state = verified` means **automation_verified** only.  
4. Evidence may become `contradicted` after a failed step.  
5. Docs never call Harnis an OS sandbox ([F8](FAILURE_CASES.md) family).

## Hardening backlog (priority)

| P | Item | Status |
| --- | --- | --- |
| P0 | Keep isolate-on-execute default; document disable flag | landed |
| P0 | Contradiction evidence on verify fail | landed |
| P1 | This checklist + SECURITY cross-links | landed (Stage-3) |
| P2 | Optional container profile for verify (`--profile container`: Docker/Podman `--network none --read-only`) | landed |
| P2 | Stronger secret detectors (Shannon entropy + known token formats: `ghp_`, `github_pat_`, `AKIA`, `xox*`, `sk-*`, PEM headers) | landed |
| P3 | Third-party review of path sandbox | open (external) |

## Reporter path

Private disclosure to repository maintainers before public write-ups. Do not file “sandbox escape” issues against authorize-gate behavior alone — that is documented non-scope.

## Related

- [`SECURITY.md`](../SECURITY.md)  
- [`DEPTH.md`](DEPTH.md) — authorize ≠ sandbox  
- [`trusted-agent-loop.md`](trusted-agent-loop.md)  
- [`extensions.md`](extensions.md) — do not extend verify without isolation + honesty flags  
