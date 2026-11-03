# Witnis

**An engineering witness for AI coding agents.**

Map the repo. Trace the blast radius. Verify with evidence — not vibes.

Witnis pairs with [Harnis](https://github.com/L00PLeGeNd/Harnis): the *harness* limits what an agent can **do**; the *witness* grounds what an agent can **claim**.

[![CI](https://github.com/L00PLeGeNd/Witnis/actions/workflows/ci.yml/badge.svg)](https://github.com/L00PLeGeNd/Witnis/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/rust-core-orange.svg)](docs/rust-migration.md)
[![Release](https://img.shields.io/github/v/release/L00PLeGeNd/Witnis.svg)](https://github.com/L00PLeGeNd/Witnis/releases)

---

## Why it exists

Agents can edit files, run tests, and sound sure of themselves. They still often:

- treat a text hit as a **typed symbol**
- miss call, inherit, and override edges that define real blast radius
- equate “tests passed once” with proof — without a **gated** verify path
- answer without a machine-checkable **evidence status**

Grep and RAG find strings. They do not witness claims.

Witnis is local-first: index the tree into SQLite, answer through shared contracts, and keep Core facts free of any LLM.

| Piece | Role |
|---|---|
| **Index** | Symbols and relations on disk — no cloud |
| **Evidence envelope** | Every reply carries `status`, `evidence`, `limitations` |
| **Impact** | Callers, related tests, change radius |
| **Gated verify** | Runs only with `--execute` and `WITNIS_ALLOW_VERIFY=1` |
| **One Core** | Same behavior on **CLI · MCP · SDK · Studio** |

```mermaid
flowchart LR
  Repo[Repository] --> Index[SQLite index]
  Index --> Search[search / LSP]
  Index --> Trace[trace / impact]
  Trace --> Plan[plan-verify]
  Plan --> Gate{authorized?}
  Gate -->|no| Blocked[blocked]
  Gate -->|yes| Verify[verify]
  Index --> Studio[Studio]
  Index --> MCP[MCP]
```

---

## Quick start

```bash
git clone https://github.com/L00PLeGeNd/Witnis.git
cd Witnis
pip install -e ".[dev,lsp]"

python -m witnis index fixtures/mini_py
python -m witnis search login --json
python -m witnis trace login --json
python -m witnis impact login --json
python -m witnis lsp AuthService --json
python -m witnis plan-verify --target login
python -m witnis studio --target login --out .witnis/studio.html

pytest -q
python -m witnis bench --suite public
```

Extras: `.[lsp]` (Jedi), `.[rust]` (maturin), or `.[all]`.

---

## How agents should use it

1. **Index** the repo (refresh after large edits)
2. **Search** the symbol before changing it
3. **Trace** callers, inheritance, decorators
4. **Impact** and related tests before the edit
5. **plan-verify**, then **verify --execute** only with explicit auth
6. Open **Studio** or an evidence bundle for review

Longer playbook: [`examples/agent-playbook.md`](examples/agent-playbook.md)

### Envelope shape

CLI, MCP, and SDK share the same JSON shape:

```json
{
  "status": "success",
  "repository": { "name": "mini_py", "root_path": "..." },
  "result": {},
  "evidence": [
    {
      "type": "symbol",
      "status": "observed",
      "path": "auth.py",
      "line": 12,
      "name": "AuthService.login"
    }
  ],
  "limitations": ["Search is name/path FTS+LIKE, not embeddings"],
  "generated_at": "2026-11-03T12:00:00Z"
}
```

Statuses encode uncertainty: `observed` · `derived` · `verified` · `unverified` · `contradicted` · `stale` · …

Contracts: [`docs/contracts-v1.md`](docs/contracts-v1.md)

---

## Surfaces

| Layer | What you get |
|---|---|
| **CLI** | `index`, `search`, `trace`, `impact`, `plan-verify`, `verify`, `studio`, `lsp`, `bench`, `compare-baselines`, … |
| **MCP** | `repo_search`, `trace_symbol`, `analyze_impact`, `run_verification`, `query_lsp`, `render_studio`, … |
| **SDK** | `from witnis.sdk import index_repository, repo_search, trace_symbol, …` |
| **Studio** | Static HTML (graph / evidence / report), `en` `zh` `pt` `fr` `ru` |
| **Languages** | Python (AST) · JS/TS · Go · Java (shallow) |
| **LSP** | Jedi · index fallback · optional Pyright diagnostics |

### Against simple baselines

| Approach | Typed symbols | Call / impact | Evidence | Gated verify |
|---|---|---|---|---|
| `git grep` / naive scan | — | — | — | — |
| Regex `def` / `class` | shallow | — | — | — |
| **Witnis** | yes | yes | yes | yes |

```bash
python -m witnis compare-baselines fixtures/mini_py --out docs/benchmarks/local-v1.md
```

---

## Cursor MCP

Index the repo first, then point MCP at the DB:

```json
{
  "mcpServers": {
    "witnis": {
      "command": "python",
      "args": ["-m", "witnis", "mcp", "--db", "/ABS/PATH/TO/Witnis/.witnis/index.sqlite"],
      "env": {
        "WITNIS_DB": "/ABS/PATH/TO/Witnis/.witnis/index.sqlite"
      }
    }
  }
}
```

Sample file: [`examples/mcp.cursor.example.json`](examples/mcp.cursor.example.json)

Agents should call `list_capabilities` before assuming tool names.

---

## Security posture

Read-only by default.

- Paths sandboxed to the indexed root (symlink escapes rejected)
- Sensitive names (`.env`, `*.pem`, `*.key`, …) skipped or flagged
- Secret-like values redacted in previews
- Verify stays blocked until you authorize it
- Repo prose is untrusted input (prompt-injection aware)

More: [`SECURITY.md`](SECURITY.md)

---

## Benchmarks

CI keeps the public suite green:

```bash
python -m witnis bench --suite local
python -m witnis bench --suite public
```

| Suite | Scope |
|---|---|
| Local | `fixtures/mini_py` regressions |
| Public | `mini_py` + Go / JS / Java smokes + polyglot `fixtures/public_svc` |

Public score (v1.8.0): **21 / 21**.  
Method: [`docs/benchmarks/PUBLIC.md`](docs/benchmarks/PUBLIC.md) · History: [`docs/benchmarks/public-scoreboard.md`](docs/benchmarks/public-scoreboard.md)

---

## Layout

```
adapters   CLI · MCP · SDK · Studio
    │
core       index · search · trace · impact · verify · evidence · LSP
    │
native     optional witnis._native (PyO3) → witnis-core (Rust)
    │
store      SQLite + FTS5 (symbols, relations, snapshots)
```

Python adapters install with plain `pip`. Rust speeds discover, digests, RustPython AST, and SQLite index/search. If `_native` is missing, Python paths still work.

### Optional Rust tools

```bash
cargo test -p witnis-core
cargo run -p witnis-cli -- discover fixtures/mini_py
cargo run -p witnis-cli -- index fixtures/mini_go --db .witnis/rust-go.sqlite --full
cargo run -p witnis-cli -- search Login --db .witnis/rust-go.sqlite
cargo run -p witnis-cli -- overview --db .witnis/rust-go.sqlite

maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install dist-native/witnis-*.whl
```

| Env | Meaning |
|---|---|
| `WITNIS_RUST_INDEX=1` | Always use the Rust indexer |
| `WITNIS_RUST_INDEX=auto` | Rust indexer when `_native` is loaded |
| *(default)* | Rust for non-`.py` trees; Python AST for `.py` |
| `WITNIS_ALLOW_VERIFY=1` | Allow `verify --execute` |

See [`docs/rust-migration.md`](docs/rust-migration.md).

---

## Docs

| Doc | Contents |
|---|---|
| [`docs/contracts-v1.md`](docs/contracts-v1.md) | Stable CLI / MCP / envelope |
| [`docs/rust-migration.md`](docs/rust-migration.md) | Rust migration phases |
| [`docs/benchmarks/PUBLIC.md`](docs/benchmarks/PUBLIC.md) | Public bench method |
| [`SECURITY.md`](SECURITY.md) | Security defaults |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Dev loop and PR expectations |
| [`CHANGELOG.md`](CHANGELOG.md) | Releases |
| [`examples/agent-playbook.md`](examples/agent-playbook.md) | Agent usage |

---

## Status

Ready for local Python-first agent work:

**index → search / trace / impact → gated verify → Studio / MCP**

Still ahead: a single Rust `witnis` binary, stronger language servers, larger third-party corpora.

Latest: [v1.8.0](https://github.com/L00PLeGeNd/Witnis/releases/tag/v1.8.0)

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Keep `pytest` and `witnis bench --suite public` green.

## License

Apache-2.0 — [`LICENSE`](LICENSE).
