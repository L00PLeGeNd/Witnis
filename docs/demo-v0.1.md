# Witnis v0.1 demo (local)

Recorded 2026-11-03 on Windows / Python 3.12.

```text
pip install -e ".[dev]"
pytest -q
# 2 passed

python -m witnis index fixtures/mini_py
# indexed repo=mini_py files=2 symbols=4 db=...\Witnis\.witnis\index.sqlite

python -m witnis overview
# repository=mini_py root=...\fixtures\mini_py files=2 symbols=4

python -m witnis search login
# method    AuthService.login   auth.py:7-8
```

Success criteria for Foundation met locally. No public GitHub publish.
