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
| 6 | SQLite index writer in Rust (`index` CLI + PyO3) | done |
| 6b | Deeper Python shallow + Rust `search` | done |
| 6c | Rust Python via `rustpython-parser` AST | done |
| 6d | Rust `overview` + CI + search prefer-native | done |
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
cargo run -p witnis-cli -- index fixtures/mini_java --db .witnis/rust-java.sqlite --full
cargo run -p witnis-cli -- search login --db .witnis/rust-java.sqlite
cargo run -p witnis-cli -- overview --db .witnis/rust-java.sqlite

# optional Python wheel
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install dist-native/witnis-*.whl
```

Python `index_repository` uses the Rust writer when:
- `WITNIS_RUST_INDEX=1`, or
- `WITNIS_RUST_INDEX=auto` and `witnis._native` is loaded, or
- the tree has no `.py` files.

Rust Python parsing uses `rustpython-parser` AST. Pure-Python AST remains default for `.py` trees unless opted in.
