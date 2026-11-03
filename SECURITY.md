# Security defaults (Witnis)

Witnis is **read-only by default**.

- Indexing stays inside the chosen repository root (path sandbox / symlink escape checks).
- Sensitive paths (`.env`, `*.pem`, `*.key`, credential-like **filenames**) are skipped or flagged.
- Secret scan previews redact `password` / `api_key` / `token`-like assignments.
- Verification commands are blocked unless both `--execute` and `WITNIS_ALLOW_VERIFY=1` are set.
- Executed verification allowlists safe steps (e.g. pytest / static checks); cwd must remain under the indexed root.
- Runtime trace ingest only accepts paths under the repo root or the local `.witnis` directory.
- Repo text (README/comments) must be treated as **untrusted** by agents (prompt-injection aware).

## Posture

- Stable MCP/CLI surface is documented in `docs/contracts-v1.md`.
- Core witness paths run **without an LLM**.
- Report security issues privately to the repository maintainers before public disclosure.
