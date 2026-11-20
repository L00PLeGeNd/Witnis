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

The **default** `worktree` profile is still not a hardened OS jail. Authorized worktree verify can still:

- use network if a subprocess does (`network: deny-hint` only)
- spawn further processes
- mutate files inside the disposable worktree

`--profile container` (Docker or Podman) is stricter and **is shipped**: `--network none`, read-only root, source mounted `:ro`, bytecode/pytest cache on tmpfs. It fails closed (exit 127) when no runtime is present. The default image `python:3.12-slim` has no pytest; build `docker/verify.Dockerfile` and set `WITNIS_VERIFY_IMAGE`.

Documented path boundaries and command allowlists are **policy intent**. They are not a completed third-party security audit.

Shipped hardening (default on execute, disable with `WITNIS_VERIFY_ISOLATE=0`):

- Disposable git worktree (or tree copy fallback)
- Scrubbed child environment + network-deny **hint** (worktree) or `--network none` (container)
- Per-step timeouts
- Pre/post filesystem snapshot diff in the report
- Existing argv allowlist (pytest / compileall) and path sandbox
- Optional `--profile container` as above

Still **not** shipped: cgroup memory/CPU caps, seccomp/AppArmor profiles, a third-party sandbox audit. See [`docs/DEPTH.md`](docs/DEPTH.md).

## Posture

- Stable MCP/CLI surface is documented in `docs/contracts-v1.md`.
- Core witness paths run **without an LLM**.
- Report security issues via GitHub private vulnerability reporting on this repository, before public disclosure.
- Hardening checklist / backlog: [`docs/security-hardening.md`](docs/security-hardening.md).
