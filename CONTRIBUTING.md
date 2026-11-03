# Contributing to Witnis

## Local loop

```bash
pip install -e ".[dev,lsp]"
cargo test -p witnis-core
pytest -q
python -m witnis bench --suite public
```

Optional native acceleration:

```bash
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install --force-reinstall dist-native/witnis-*.whl
```

## Rules

1. Keep evidence envelopes and MCP/CLI contracts stable (`docs/contracts-v1.md`).
2. Prefer deterministic Core changes over LLM glue.
3. Python adapters stay usable when `witnis._native` is missing.
4. Do not commit secrets, wheels, `target/`, or `*.pyd`.
5. Public bench (`benchmarks/public/tasks.json`) must stay green.

## Pull requests

- One concern per PR when possible.
- Include the verification commands you ran.
