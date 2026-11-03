# DONE — Witnis 1.5.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## Rust progress
- `witnis-core`: discover, sandbox, hash, scan digests, shallow parsers, **SQLite index writer**
- `witnis-py`: PyO3 `_native` (`list_source_files`, `scan_digests`, `parse_shallow`, `index_repo`)
- `witnis-cli`: `witnis-core discover|scan|index`
- Python index uses Rust for non-Python trees (or `WITNIS_RUST_INDEX=1`)

## Still Python
- Deep Python AST analysis, verify engine, MCP/CLI/Studio adapters
- Full Python index path when native missing or mixed `.py` trees (default)

## Verify locally before push
```bash
cargo test -p witnis-core
cargo build -p witnis-cli
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install --force-reinstall dist-native/witnis-*.whl
pytest -q
python -m witnis bench --suite public
```
