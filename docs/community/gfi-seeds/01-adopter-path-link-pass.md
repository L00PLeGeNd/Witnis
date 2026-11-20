# GFI: Adopter-path link pass

**Labels:** `good first issue`, `docs`

## Goal

Walk [`docs/adopter-path.md`](../../adopter-path.md) and ensure every relative link resolves; add one missing cross-link from README “Still ahead” or docs index if helpful.

## Non-goals

No CLI behavior changes.

## Acceptance

```bash
# manually open each linked path from adopter-path.md
pytest -q tests/test_loop_init.py   # sanity; should still pass
```

PR description lists links you checked.
