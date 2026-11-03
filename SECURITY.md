# Security defaults (Witnis)

Witnis is **read-only by default**.

- Indexing stays inside the chosen repository root (path sandbox / symlink escape checks).
- Sensitive paths (`.env`, `*.pem`, `*.key`, credential-like **filenames**) are skipped or flagged.
- Secret scan previews redact `password` / `api_key` / `token`-like assignments.
- Verification commands are blocked unless both `--execute` and `WITNIS_ALLOW_VERIFY=1` are set.
- Executed verification allowlists safe steps (e.g. pytest / static checks); cwd must remain under the indexed root.
- Runtime trace ingest only accepts paths under the repo root or the local `.witnis` directory.
- Repo text (README/comments) must be treated as **untrusted** by agents (prompt-injection aware).

## Authorize gate ≠ execution sandbox

`WITNIS_ALLOW_VERIFY=1` plus `--execute` is an **authorization gate**: the user opted in.

It is **not** a hardened OS/container sandbox. Authorized verify can still:

- touch files outside intent if a step escapes allowlist assumptions
- use network if a subprocess does
- spawn further processes
- mutate the user environment within process limits

Documented path boundaries and command allowlists are **policy intent**. They are not a completed third-party security audit.

Shipped hardening (default on execute, disable with `WITNIS_VERIFY_ISOLATE=0`):

- Disposable git worktree (or tree copy fallback)
- Scrubbed child environment + network-deny **hint**
- Per-step timeouts
- Pre/post filesystem snapshot diff in the report
- Existing argv allowlist (pytest / compileall) and path sandbox

Still **not** shipped: true container/OS jail, cgroup memory/CPU caps, enforced network namespace. See [`docs/DEPTH.md`](docs/DEPTH.md).

## Posture

- Stable MCP/CLI surface is documented in `docs/contracts-v1.md`.
- Core witness paths run **without an LLM**.
- Report security issues privately to the repository maintainers before public disclosure.
