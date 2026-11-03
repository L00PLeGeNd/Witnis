# Gradual Rust migration

Witnis stays **Python-first for adapters** (CLI/MCP/Studio/SDK) while hot Core paths move into Rust.

## Phases

| Phase | Crate / surface | Status |
|---|---|---|
| 0 | Cargo workspace + `witnis-core` | this slice |
| 1 | Discover / path sandbox / content hash in Rust | this slice |
| 2 | PyO3 `witnis._native` optional extension | this slice |
| 3 | Index write path / SQLite helpers | next |
| 4 | Parsers (Python AST stays in Py; Go/JS/Java regex → Rust) | next |
| 5 | Optional `witnis` Rust CLI binary sharing core | later |

## Rules

1. Evidence envelopes and tool contracts stay stable (`docs/contracts-v1.md`).
2. Python remains the default install; Rust is additive (`witnis[rust]` / maturin when enabled).
3. If the native module is missing, Python implementations keep working (feature-flag / try-import).
4. Prefer porting **deterministic, CPU-bound, pure** logic first — not Typer/MCP glue.

## Build

```bash
# toolchain
rustup default stable

# native tests
cargo test -p witnis-core

# optional Python wheel (when maturin wired)
pip install -e ".[rust]"
```
