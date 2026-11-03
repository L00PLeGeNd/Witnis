# Witnis v1.0 local demo

## Install

```bash
pip install -e ".[dev]"
python -m witnis version   # 1.0.0
```

## Index + witness

```bash
python -m witnis index fixtures/mini_py
python -m witnis status --json
python -m witnis search login --json
python -m witnis trace login --json
python -m witnis impact login --json
```

## Studio + baselines

```bash
python -m witnis studio --target login --out .witnis/studio.html
python -m witnis compare-baselines fixtures/mini_py --out docs/benchmarks/local-v1.md
python -m witnis bench
```

## Verification gate

```bash
python -m witnis plan-verify --target login
python -m witnis verify --target login          # blocked without auth
# WITNIS_ALLOW_VERIFY=1 python -m witnis verify --execute --target login
```

## Contracts

See `docs/contracts-v1.md`. Public GitHub remains intentionally gated.
