# DONE — Witnis 1.4.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## Rust progress
- `witnis-core`: discover, sandbox, hash, scan digests, Go/JS/Java parse
- `witnis-py`: PyO3 `_native` (`list_source_files`, `scan_digests`, `parse_shallow`, …)
- `witnis-cli`: `witnis-core discover|scan`
- Python index uses native path when available

## Still Python
- AST Python analysis, verify engine, MCP/CLI/Studio adapters, SQLite store

## Verify locally before push
```bash
cargo test -p witnis-core
cargo build -p witnis-cli
maturin build -m crates/witnis-py/Cargo.toml --out dist-native
pip install --force-reinstall dist-native/witnis-*.whl
pytest -q
python -m witnis bench --suite public
```
