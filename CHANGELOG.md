# Changelog

## 1.5.0

- Rust SQLite index writer (`store` + `index_repository`) for Go / JS / Java / shallow Python
- `witnis-core` CLI: `index` (alongside `discover` / `scan`)
- PyO3 `index_repo`; Python index prefers Rust for non-`.py` trees or `WITNIS_RUST_INDEX=1`
- Migration phase 6 done

## 1.4.0

- Rust shallow parsers for Go / JS / Java + batch `scan_digests`
- Index prefers Rust digests/parsers when `witnis._native` is present
- `witnis-core` Rust CLI: `discover` / `scan`
- Migration doc updated through phase 5

## 1.3.0

- Cargo workspace: `witnis-core` + PyO3 `witnis-py`
- Rust discover / sandbox / sha256 with Python fallback

## 1.2.0

- Public release: evidence witness CLI/MCP/Studio, multi-lang shallow, LSP optional
