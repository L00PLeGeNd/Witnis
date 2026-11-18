# Changelog

## 1.10.0

- **Trusted Agent Loop:** `witnis pr-gate` (three-dot / merge-base PR impact + markdown/JSON)
- Git helpers: `git_merge_base`, `git_name_status_triple_dot`, `git_diff_hunks_range`
- Composite Action `.github/actions/pr-gate` + consumer example + CI dogfood job
- Verify honesty: `automation_verified` / `skipped_only`; `contradicted` evidence on failed steps; worktree pin to `--revision`
- MCP×Harnis templates; `docs/trusted-agent-loop.md`; ROADMAP narrative update
- `witnis loop-init` — one-shot Trusted Agent Loop bootstrap (Harnis wrap MCP + policy + index)
- Harnis scan catalog includes `witnis` → `coding-agent` preset

## 1.9.1

- `witnis scene` — auth token-refresh story card (engineering results, not MCP names)
- `witnis experiment` — reproducible grep vs Witnis analysis A/B pack + published JSON
- `fixtures/auth_refresh` demo; Claude Code / Codex MCP examples
- README answers “why not bare agent?” with measured cold-install timing

## 1.9.0

- Java Spring-aware relations: `implements`, field/ctor `injects`, typed field calls
- Ground-truth suite: `witnis bench --suite ground-truth` + labeled DI fixture
- Verify isolation by default: worktree/copy, scrubbed env, FS diff (`WITNIS_VERIFY_ISOLATE`)
- Engine parity tests in CI; agent-effect experiment protocol scaffold
- Honest depth docs vs SCIP/LSIF/Kythe bar

## 1.8.1

- `witnis up` — index a repo then print a `look` card
- `witnis look` one-shot witness card; `witnis demo` first-run
- Short aliases: `plan`, `tests`, `baselines`; positional targets for `plan` / `verify` / `studio`
- README & playbook use short `witnis …` commands

## 1.8.0

- GitHub Actions CI (Rust + Python + public bench)
- LSP: optional Pyright/BasedPyright diagnostics on top of Jedi + index
- `repo_search` prefers native Rust FTS when available
- Rust CLI `overview`; `WITNIS_RUST_INDEX=auto`
- Expanded `fixtures/public_svc` + public bench P20–P21
- CONTRIBUTING + polished README/scoreboard

## 1.7.0

- Rust Python parse uses `rustpython-parser` AST
- `fixtures/public_svc` polyglot corpus; public bench expanded
- LSP Jedi + index-backed fallback
- Search merges FTS + LIKE for qualified names

## 1.6.0

- Deeper Rust Python parse + Rust symbol search
- `witnis-core search`, PyO3 `search_db`

## 1.5.0

- Rust SQLite index writer + CLI `index` + PyO3 `index_repo`

## 1.4.0

- Rust shallow parsers for Go / JS / Java + batch `scan_digests`
- `witnis-core` CLI: `discover` / `scan`

## 1.3.0

- Cargo workspace + PyO3 `witnis-py` discover bridge

## 1.2.0

- Public release: evidence witness CLI/MCP/Studio, multi-lang shallow, LSP optional
