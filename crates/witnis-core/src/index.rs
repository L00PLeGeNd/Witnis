use std::collections::HashSet;
use std::fs;
use std::path::Path;

use serde::Serialize;

use crate::parse::{go, java, js, python, Relation, Symbol};
use crate::sandbox::SandboxError;
use crate::scan::scan_source_digests;
use crate::store::Store;

#[derive(Debug, Clone, Serialize)]
pub struct IndexStats {
    pub repository: String,
    pub files: i64,
    pub symbols: i64,
    pub db_path: String,
    pub updated_files: i64,
    pub skipped_unchanged: i64,
    pub removed_files: i64,
    pub relations: i64,
    pub mode: String,
    pub backend: String,
}

fn parse_file(path: &Path, rel_path: &str, source: &str) -> (Vec<Symbol>, Vec<Relation>) {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    match ext.as_str() {
        "py" => (
            python::parse_symbols(source, rel_path),
            python::parse_relations(source, rel_path),
        ),
        "go" => {
            let mut edges = go::parse_imports(source, rel_path);
            edges.extend(go::parse_calls(source, rel_path));
            (go::parse_symbols(source, rel_path), edges)
        }
        "java" => {
            let mut edges = java::parse_imports(source, rel_path);
            edges.extend(java::parse_calls(source, rel_path));
            (java::parse_symbols(source, rel_path), edges)
        }
        "js" | "jsx" | "ts" | "tsx" | "mjs" | "cjs" => {
            let mut edges = js::parse_imports(source, rel_path);
            edges.extend(js::parse_calls(source, rel_path));
            (js::parse_symbols(source, rel_path), edges)
        }
        _ => (Vec::new(), Vec::new()),
    }
}

/// Index a repository into SQLite using Rust discover/parse/store.
///
/// Python uses indent-aware shallow parse (methods/inherits/decorators/calls);
/// full AST depth remains available via the Python indexer.
pub fn index_repository(
    root: &Path,
    db_path: &Path,
    incremental: bool,
) -> Result<IndexStats, SandboxError> {
    if !root.is_dir() {
        return Err(SandboxError::Io(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Not a directory: {}", root.display()),
        )));
    }
    let root = root.canonicalize().unwrap_or_else(|_| root.to_path_buf());
    let store = Store::open(db_path)?;
    let repo_id = store.upsert_repository(&root)?;
    let digests = scan_source_digests(&root)?;

    let mut all_relations: Vec<Relation> = Vec::new();
    let mut file_payload: Vec<(String, String, Vec<Symbol>)> = Vec::new();
    for row in &digests {
        let source = match fs::read_to_string(&row.path) {
            Ok(s) => s.trim_start_matches('\u{feff}').to_string(),
            Err(_) => continue,
        };
        let (symbols, relations) = parse_file(&row.path, &row.rel_path, &source);
        all_relations.extend(relations);
        file_payload.push((row.rel_path.clone(), row.sha256.clone(), symbols));
    }

    let repo_name = root
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("repo")
        .to_string();

    if !incremental {
        // Full rebuild: drop existing file rows, then write fresh payload.
        let _ = store.delete_files_not_in(repo_id, &HashSet::new())?;
        for (rel, hash, symbols) in &file_payload {
            store.upsert_file_symbols(repo_id, rel, hash, symbols)?;
        }
        let rel_count = store.replace_relations(repo_id, &all_relations)? as i64;
        store.rebuild_fts(repo_id)?;
        let files = store.file_count(repo_id)?;
        let symbols = store.symbol_count(repo_id)?;
        store.insert_index_snapshot(repo_id, files, symbols, rel_count, files, 0, 0, "full")?;
        return Ok(IndexStats {
            repository: repo_name,
            files,
            symbols,
            db_path: db_path.to_string_lossy().into_owned(),
            updated_files: files,
            skipped_unchanged: 0,
            removed_files: 0,
            relations: rel_count,
            mode: "full".into(),
            backend: "rust".into(),
        });
    }

    let existing = store.file_hashes(repo_id)?;
    let mut keep_paths: HashSet<String> = HashSet::new();
    let mut updated = 0i64;
    let mut skipped = 0i64;
    for (rel, hash, symbols) in &file_payload {
        keep_paths.insert(rel.clone());
        if existing.get(rel).map(|h| h == hash).unwrap_or(false) {
            skipped += 1;
            continue;
        }
        store.upsert_file_symbols(repo_id, rel, hash, symbols)?;
        updated += 1;
    }
    let removed = store.delete_files_not_in(repo_id, &keep_paths)? as i64;
    let rel_count = store.replace_relations(repo_id, &all_relations)? as i64;
    store.rebuild_fts(repo_id)?;
    let files = store.file_count(repo_id)?;
    let symbols = store.symbol_count(repo_id)?;
    store.insert_index_snapshot(
        repo_id,
        files,
        symbols,
        rel_count,
        updated,
        skipped,
        removed,
        "incremental",
    )?;
    Ok(IndexStats {
        repository: repo_name,
        files,
        symbols,
        db_path: db_path.to_string_lossy().into_owned(),
        updated_files: updated,
        skipped_unchanged: skipped,
        removed_files: removed,
        relations: rel_count,
        mode: "incremental".into(),
        backend: "rust".into(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn indexes_go_fixture_like_tree() {
        let dir = tempdir().unwrap();
        fs::write(
            dir.path().join("auth.go"),
            "package auth\ntype AuthService struct{}\nfunc (a *AuthService) Login() bool { return true }\n",
        )
        .unwrap();
        let db = dir.path().join("index.sqlite");
        let stats = index_repository(dir.path(), &db, false).unwrap();
        assert!(stats.files >= 1);
        assert!(stats.symbols >= 2);
        assert_eq!(stats.backend, "rust");
    }
}
