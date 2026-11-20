# Contributing to Witnis

## Local loop

```bash
pip install -e ".[dev,lsp]"
cargo test -p witnis-core
pytest -q
python -m witnis bench --suite public
```

Optional container verify (needs Docker/Podman; image includes pytest):

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

1. Keep evidence envelopes and MCP/CLI contracts stable (`docs/contracts-v1.md`).
2. Prefer deterministic Core changes over LLM glue.
3. Python adapters stay usable when `witnis._native` is missing.
4. Do not commit secrets, wheels, `target/`, or `*.pyd`.
5. Public bench (`benchmarks/public/tasks.json`) must stay green — and new claims must not greenwash known misses ([`docs/benchmarks/miss-cases.md`](docs/benchmarks/miss-cases.md)).
6. Extend only at documented seams ([`docs/extensions.md`](docs/extensions.md)).

## First contribution

1. Read [`docs/adopter-path.md`](docs/adopter-path.md) (how the product is meant to be used).  
2. Pick a [`good first issue`](https://github.com/L00PLeGeNd/Witnis/labels/good%20first%20issue) or a seed from [`docs/community/gfi-seeds/`](docs/community/gfi-seeds/).  
3. Pipeline for maintainers: [`docs/community/good-first-issue-pipeline.md`](docs/community/good-first-issue-pipeline.md).

Showcase / adopters: [`docs/SHOWCASE.md`](docs/SHOWCASE.md) · [`ADOPTERS.md`](ADOPTERS.md).  
Committer path: [`docs/community/committer-growth.md`](docs/community/committer-growth.md).

## Pull requests

- One concern per PR when possible.
- Include the verification commands you ran.
- Do not break `docs/contracts-v1.md` unless the issue explicitly allows it.
