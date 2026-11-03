# DONE — Witnis 1.8.1

Public repo: https://github.com/L00PLeGeNd/Witnis

## This release
- Short CLI: `look`, `demo`, `plan` / `tests` / `baselines`
- Docs are MCP-host neutral (not tied to one editor)
- CI, RustPython AST, public_svc, LSP stack from 1.8.0

## Verify before publish
```bash
cargo test -p witnis-core
cargo build -p witnis-cli --release
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pytest -q
python -m witnis bench --suite public
```
