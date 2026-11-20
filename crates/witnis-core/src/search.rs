use std::path::Path;

use crate::sandbox::SandboxError;
use crate::store::{SearchHit, Store};

/// Open a Witnis SQLite DB and search symbols (FTS5 + LIKE fallback).
pub fn search_symbols(
    db_path: &Path,
    query: &str,
    limit: usize,
) -> Result<Vec<SearchHit>, SandboxError> {
    let store = Store::open(db_path)?;
    store.search(query, limit)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::index_repository;
    use std::path::PathBuf;

    #[test]
    fn search_finds_go_login() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/mini_go");
        let db = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../.witnis/test-search-go.sqlite");
        let _ = std::fs::remove_file(&db);
        index_repository(&root, &db, false).expect("index");
        let hits = search_symbols(&db, "Login", 10).expect("search");
        assert!(hits.iter().any(|h| h.name == "Login"), "{hits:?}");
        let _ = std::fs::remove_file(&db);
    }
}
