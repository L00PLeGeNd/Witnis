# Gradual Rust migration

Witnis stays **Python-first for adapters** (CLI/MCP/Studio/SDK) while hot Core paths move into Rust.

## Phases

| Phase | Crate / surface | Status |
|---|---|---|
| 0 | Cargo workspace + `witnis-core` | done |
| 1 | Discover / path sandbox / content hash | done |
| 2 | PyO3 `witnis._native` optional extension | done |
| 3 | Batch digests for index (`scan_source_digests`) | done |
| 4 | Shallow Go / JS / Java parsers in Rust | done |
| 5 | `witnis-core` Rust CLI (`discover` / `scan`) | done |
| 6 | SQLite index writer in Rust | next |
| 7 | Full `witnis` Rust binary sharing contracts | later |

## Rules

1. Evidence envelopes and tool contracts stay stable (`docs/contracts-v1.md`).
2. Python remains the default install; Rust is additive (`witnis[rust]` / maturin).
3. If the native module is missing, Python implementations keep working.
4. Prefer porting **deterministic, CPU-bound, pure** logic first — not Typer/MCP glue.

## Build

```bash
rustup default stable
cargo test -p witnis-core
cargo run -p witnis-cli -- discover fixtures/mini_py
cargo run -p witnis-cli -- scan fixtures/mini_go

# optional Python wheel
maturin build -m crates/witnis-py/Cargo.toml --out dist-native
pip install dist-native/witnis-*.whl
```
