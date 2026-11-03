# DONE — Witnis 1.3.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## This slice — Rust migration start
- Cargo workspace: `witnis-core`, `witnis-py` (PyO3)
- Rust: discover / sandbox / sha256
- Python `discover.py` prefers `witnis._native` when built
- Docs: `docs/rust-migration.md`

## Usability
Still usable end-to-end in pure Python. Optional native accel via:

```bash
cargo test -p witnis-core
maturin build -m crates/witnis-py/Cargo.toml --out dist-native
pip install dist-native/witnis-*.whl
```

## Next Rust phases
Index/SQLite helpers → parsers → optional Rust CLI
