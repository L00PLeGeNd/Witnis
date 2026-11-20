# Changelog

## Unreleased

- Public product line: PR comment is the screenshot; MCP default tools are `index` / `look` / `impact` / `verify` (`WITNIS_MCP_EXPERIMENTAL=1` for the rest); masthead says 4 tools, not 34
- GitHub Action is zero-config besides checkout; `pip install witnis` / `uvx witnis` (PyPI 1.11.0)
- README lead is the 15s lie/blocked/ran loop (`caught-lying.svg`); search name **witnis-dev** (not witnis.se); seatbelt included in one install

## 1.11.0

- Phase 7.1 Rust Core parity: port Java Spring DI (`injects`), `uses_type`, and typed field `calls` into `crates/witnis-core/src/parse/java.rs`, plus `witnis-core impact` CLI/library support
- Container verification profile (`witnis verify --execute --profile container` / `WITNIS_VERIFY_PROFILE=container`): rootless Docker/Podman `--network none --read-only` + `/tmp` tmpfs mount
- Security hardening (P2): Shannon entropy calculation + known token format redaction (`ghp_`, `github_pat_`, `AKIA`, `xox*`, `sk-*`, PEM headers) in `witnis.core.security`
- Fix: `impact` / `pr-gate` reported each Python call site twice (qualified `pkg.mod.fn` and bare `fn` aliases); `_dedupe_edges` now collapses alias pairs while keeping distinct receivers (`Owner.getName` vs `Pet.getName`)
- Fix: Windows Rust index stored `\\?\`-prefixed repo roots, so Python's revision stamp created a second, empty repository row and Go/JS-heavy repos showed 0 symbols
- Fix: related-test discovery only knew Python test layouts and scanned the first 500 relations; now recognizes Java/Go/JS test paths and queries relations by target. Verify plans still pass only `.py` tests to pytest
- `witnis look` groups callers by source with their call-site lines
- Rebuild README figures from `scripts/render_readme_svgs.py`: `blast-radius.svg` (real `witnis impact Person` on spring-petclinic vs `git grep`), `trusted-agent-loop.svg` (real look/impact/plan/verify output for `redact_text`), static masthead. Tokens are bound to the drawn paths via `mpath`; labels are width-checked at build time
- README: correct the Person JSON shape (`transitive`, not `indirect`/`via`), the MCP tool list (34 tools), and the PetClinic table (expected items, not tasks)
- `witnis impact` accepts `--limit` (default 50), matching MCP `analyze_impact` and `witnis-core impact`
- `_dedupe_edges` also collapses a same-site `calls`+`references` pair, keeping `calls` and the longer target
- Container profile: fail closed (exit 127) without a runtime; bytecode/pytest cache on tmpfs (`PYTHONPYCACHEPREFIX`); pytest image via `docker/verify.Dockerfile` + `WITNIS_VERIFY_IMAGE`
- Hand-crafted `docs/home.html` + `witnis home` (CSS ambient/enter motion; no AI banner art)
- README masthead/loop/envelope as authored SVG; drop generative hero images
- PetClinic GT follow-up from FYLGls AI review: SCOPE + blind-pack, expand `h_impact_person` Indirect, drop test paths from typed Indirect, clearer expected-item scoring notes — still **not** `human_dual`
- Package `studio/home.html` + SVG assets so `witnis home` works after `pip install`; SECURITY.md documents shipped container profile vs worktree deny-hint

## 1.10.1

- Java `uses_type` + impact Indirect via subclass typed users — mitigates **F1**; PetClinic human GT **18/18** on pin
- Harden **F2/F3/F4**: auto GT noise filter, Java self-call drop, transitive call-follow marked `uncertain` + short-leaf skip
- Git subprocess UTF-8 decode (Windows GBK-safe) for `pr-gate` / diff hunks
- Annotator B blank worksheet under `benchmarks/ground-truth/adjudication/`
- Stage-3 docs + `witnis-core parity` (from prior private board)
- CI / local **bench report page**: `witnis bench --report` + `--github-summary` ([`docs/benchmarks/ci-report.md`](docs/benchmarks/ci-report.md))
- MCP directory listing payloads: `glama.json`, `server.json`, `.mcp.json`, `Dockerfile.mcp` ([`docs/mcp-listings.md`](docs/mcp-listings.md))
- Marketing drafts: Trusted Agent Loop flagship post + Harnis co-marketing kit ([`docs/marketing/`](docs/marketing/))
- Default adopter path docs: incremental refresh · PR gate · export ([`docs/adopter-path.md`](docs/adopter-path.md))
- Adopters / Showcase / good-first-issue pipeline ([`ADOPTERS.md`](ADOPTERS.md) · [`docs/SHOWCASE.md`](docs/SHOWCASE.md) · [`docs/community/`](docs/community/))
- PetClinic **human-v1** → **human-v2 adjudicated** ground-truth subset (16 tasks; maintainer second-pass, not dual-human) + Direct/Indirect impact scoring · [`docs/benchmarks/petclinic-human-v2.md`](docs/benchmarks/petclinic-human-v2.md)
- [`docs/FAILURE_CASES.md`](docs/FAILURE_CASES.md) — honest miss gallery (F1–F10)
- Cross-platform **`witnis-core`** release workflow + [`docs/BINARY.md`](docs/BINARY.md) + install scripts (full CLI remains pip)
- `witnis browser-demo` / `scene --open` — token-refresh story as browser HTML ([`docs/demo-browser.md`](docs/demo-browser.md))
- [`examples/witnis-harnis-starter/`](examples/witnis-harnis-starter/) seed + Discussion / Loop Issue templates
- CI: fix duplicate `pr-gate-dogfood` job; add push smoke; dogfood verified on PR #5

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
