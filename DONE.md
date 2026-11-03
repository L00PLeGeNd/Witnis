# DONE — Witnis 1.2.0

Public repo: https://github.com/L00PLeGeNd/Witnis

## GPT design coverage
| Requirement | Status |
|---|---|
| Evidence envelopes + statuses | done |
| Core independent of MCP (CLI/SDK/Studio adapters) | done |
| Verification gated + reports | done |
| Impact / related tests / Git-aware change tools | done |
| MCP + CLI + Studio | done |
| Local-first, no LLM required for facts | done |
| Runtime traces (optional) | done |
| LSP enrichment | done (Jedi optional) |
| Multi-language | Python deep; JS/TS, Go, Java shallow |
| Studio i18n en/zh/pt/fr/ru | done |
| Public benchmarks + methodology | done (fixture-scale) |
| Public GitHub | done |

## Usability
Ready for local agent use on Python repos via CLI/MCP. Foundation is solid (index, evidence, impact, verify gate). Not yet a full multi-language IDE replacement.

## Reproduce
```bash
pip install -e ".[dev,lsp]"
pytest -q
python -m witnis bench --suite public
```
