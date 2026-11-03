# Witnis

**Engineering witness for AI coding agents.**  
Understand the repo. Trace the blast radius. Verify with evidence — not vibes.

Sibling to [Harnis](https://github.com/L00PLeGeNd/Harnis): *Harness* constrains what an agent may **do**; *Witness* grounds what an agent may **claim**.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

## Why Witnis

Coding agents can edit files and run tests, but they still guess about structure, impact, and proof. Witnis is **local-first verification infrastructure**:

- Index symbols & relations into SQLite (no cloud required)
- Return every answer in an **evidence envelope** (`observed` / `derived` / `verified` / `stale` / …)
- Bound change impact and related tests
- Run **gated** verification (`--execute` + `WITNIS_ALLOW_VERIFY=1`)
- Serve the same Core through **CLI · MCP · SDK · Studio**

Core facts do **not** require an LLM.

## Quick start

```bash
pip install -e ".[dev]"
python -m witnis index fixtures/mini_py
python -m witnis search login --json
python -m witnis trace login --json
python -m witnis impact login --json
python -m witnis plan-verify --target login
python -m witnis studio --target login --out .witnis/studio.html
pytest -q
python -m witnis bench --suite public
```

Optional Jedi LSP enrichment:

```bash
pip install -e ".[lsp]"
python -m witnis lsp AuthService
```

## What you get

| Layer | Surface |
|---|---|
| **CLI** | `index`, `search`, `trace`, `impact`, `verify`, `studio`, `lsp`, `bench`, `compare-baselines`, … |
| **MCP** | `repo_search`, `trace_symbol`, `analyze_impact`, `run_verification`, `query_lsp`, `render_studio`, … |
| **SDK** | `from witnis.sdk import index_repository, repo_search, …` |
| **Studio** | Static HTML dashboard (graph / evidence / report), `en|zh|pt|fr|ru` |
| **Languages** | Python (deep) · JS/TS · Go · Java (shallow) |

Stable contracts: [`docs/contracts-v1.md`](docs/contracts-v1.md)

## Cursor MCP

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

Example file: [`examples/mcp.cursor.example.json`](examples/mcp.cursor.example.json)

## Security defaults

- Read-only by default
- Path sandbox + sensitive filename skips
- Verification blocked unless explicitly authorized
- Secret-like values redacted in previews

Details: [`SECURITY.md`](SECURITY.md)

## Benchmarks

```bash
python -m witnis bench --suite local
python -m witnis bench --suite public
python -m witnis compare-baselines fixtures/mini_py --out docs/benchmarks/local-v1.md
```

Methodology: [`docs/benchmarks/PUBLIC.md`](docs/benchmarks/PUBLIC.md)

## Rust core (gradual)

Hot paths are moving into Rust while Python keeps CLI/MCP/Studio adapters.

```bash
cargo test -p witnis-core
cargo run -p witnis-cli -- discover fixtures/mini_py
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install dist-native/witnis-*.whl   # optional witnis._native
```

Native accelerates discover, batch digests, and shallow Go/JS/Java parse.  
See [`docs/rust-migration.md`](docs/rust-migration.md).

## Status

**Usable today** for local Python-first agent workflows (index → search/trace/impact → gated verify → Studio/MCP).

Still deepening: Rust index/parsers, stronger LSP backends, larger public corpora.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
