# DONE — Witnis 1.8.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## This release
- CI on GitHub Actions
- RustPython AST + Rust index/search/overview
- Jedi + index + optional Pyright diagnostics
- Polyglot `fixtures/public_svc` + 21 public bench tasks
- CONTRIBUTING / scoreboard / polished README

## Verify before publish
```bash
cargo test -p witnis-core
cargo build -p witnis-cli --release
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pytest -q
python -m witnis bench --suite public
```
