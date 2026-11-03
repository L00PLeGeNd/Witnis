# DONE — Witnis 1.7.0 (local)

Public repo: https://github.com/L00PLeGeNd/Witnis

## This release
- Rust Python via `rustpython-parser` AST
- Larger public polyglot fixture `fixtures/public_svc`
- Public bench 19 tasks (mini_* + public_svc)
- LSP Jedi with index fallback

## Still later
- Full Rust `witnis` binary (phase 7)
- Stronger external LSP (pyright language server)
- Even larger third-party corpora

## Verify locally before push
```bash
cargo test -p witnis-core
cargo build -p witnis-cli --release
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pytest -q
python -m witnis bench --suite public
```
