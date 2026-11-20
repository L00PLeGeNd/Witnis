# Contributing to Witnis

## Local loop

```bash
pip install -e ".[dev,lsp]"
cargo test -p witnis-core
pytest -q
python -m witnis bench --suite public
```

Optional container verify (needs Docker/Podman):

```bash
docker build -t witnis-verify:3.12 -f docker/verify.Dockerfile docker
set WITNIS_VERIFY_IMAGE=witnis-verify:3.12
set WITNIS_ALLOW_VERIFY=1
python -m witnis verify login --execute --profile container --db <fixture-index>
```

Optional native acceleration:

```bash
maturin build -m crates/witnis-py/Cargo.toml --release --out dist-native
pip install --force-reinstall dist-native/witnis-*.whl
```

## Rules

1. Keep evidence envelopes and MCP/CLI contracts stable ([`docs/contracts-v1.md`](docs/contracts-v1.md)).
2. Prefer deterministic Core changes over LLM glue.
3. Python adapters stay usable when `witnis._native` is missing.
4. Do not commit secrets, wheels, `target/`, or `*.pyd`.
5. Public bench must stay green; do not greenwash known misses ([`docs/FAILURE_CASES.md`](docs/FAILURE_CASES.md)).
6. Extend only at documented seams ([`docs/extensions.md`](docs/extensions.md)).

## Pull requests

- One concern per PR when possible.
- Include the verification commands you ran.
- Do not break `docs/contracts-v1.md` unless the issue explicitly allows it.
