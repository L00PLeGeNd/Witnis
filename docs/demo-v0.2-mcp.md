# Witnis local demo pack

```bash
pip install -e ".[dev]"
pytest -q
# 22 passed (as of verification-plan slice)

python -m witnis index fixtures/mini_py
python -m witnis overview --json
python -m witnis search login --json
python -m witnis trace login --json
python -m witnis impact login --json
python -m witnis explain-change HEAD --json
python -m witnis plan-verify --target login
python -m witnis verify --target login
# state=blocked unless: --execute and WITNIS_ALLOW_VERIFY=1

python -m witnis mcp --db .witnis/index.sqlite
```

MCP tool names match the design spec. Still **not** published to public GitHub.
