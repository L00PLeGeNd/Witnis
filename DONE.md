# DONE — Witnis 1.6.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## Rust progress
- `witnis-core`: discover, hash, scan, shallow multi-lang parse, SQLite index, **search**
- Deeper Python shallow: `Class.method`, inherits / decorated_by / overrides / calls
- `witnis-py`: `index_repo`, `search_db`, `parse_shallow` including `python`
- `witnis-cli`: `discover|scan|index|search`

## Still Python
- Full AST Python analysis (default for `.py` trees), verify engine, MCP/CLI/Studio adapters

## Verify locally before push
```bash
cargo test -p witnis-core
cargo build -p witnis-cli --release
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pytest -q
python -m witnis bench --suite public
```
