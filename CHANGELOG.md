# Changelog

## 1.8.0

- GitHub Actions CI (Rust + Python + public bench)
- LSP: optional Pyright/BasedPyright diagnostics on top of Jedi + index
- `repo_search` prefers native Rust FTS when available
- Rust CLI `overview`; `WITNIS_RUST_INDEX=auto`
- Expanded `fixtures/public_svc` + public bench P20–P21
- CONTRIBUTING + polished README/scoreboard

## 1.7.0

- Rust Python parse uses `rustpython-parser` AST
- `fixtures/public_svc` polyglot corpus; public bench expanded
- LSP Jedi + index-backed fallback
- Search merges FTS + LIKE for qualified names

## 1.6.0

- Deeper Rust Python parse + Rust symbol search
- `witnis-core search`, PyO3 `search_db`

## 1.5.0

- Rust SQLite index writer + CLI `index` + PyO3 `index_repo`

## 1.4.0

- Rust shallow parsers for Go / JS / Java + batch `scan_digests`
- `witnis-core` CLI: `discover` / `scan`

## 1.3.0

- Cargo workspace + PyO3 `witnis-py` discover bridge

## 1.2.0

- Public release: evidence witness CLI/MCP/Studio, multi-lang shallow, LSP optional
