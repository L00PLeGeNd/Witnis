# Browser demo (token-refresh scene)

One-command, browser-openable story of the Trusted Agent Loop — not a Studio redesign.

## Run

```bash
pip install -e .   # or: pip install witnis
witnis browser-demo
# writes .witnis/browser-demo.html and opens it

witnis browser-demo --no-open --out /tmp/witnis-demo.html
witnis scene --open
```

## What you see

Brand-led page: **task → context → impact → change guidance → gated verify**, plus “why not bare agent.”  
Data is a live index of [`fixtures/auth_refresh`](../fixtures/auth_refresh/). Opening the page does **not** execute verify.

Terminal twin: [`docs/demo-auth-refresh.md`](demo-auth-refresh.md) · `witnis scene`

## Design notes

Editorial/technical composition: Fraunces brand, mono metadata, ambient grain + veil, staggered enter, `prefers-reduced-motion` respected. Studio dashboard remains `witnis studio --open` for index/graph panels.
