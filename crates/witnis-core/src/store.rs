use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};

use chrono::Utc;
use rusqlite::{params, Connection, OptionalExtension};

use crate::parse::{Relation, Symbol};
use crate::sandbox::SandboxError;

const SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    UNIQUE(repo_id, path),
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    FOREIGN KEY(file_id) REFERENCES files(id)
);
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    start_line INTEGER,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target);
CREATE TABLE IF NOT EXISTS index_snapshots (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    files INTEGER NOT NULL,
    symbols INTEGER NOT NULL,
    relations INTEGER NOT NULL,
    updated_files INTEGER,
    skipped_unchanged INTEGER,
    removed_files INTEGER,
    mode TEXT,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    name,
    path,
    kind,
    tokenize='porter'
);
"#;

pub struct Store {
    conn: Connection,
    pub db_path: PathBuf,
}

impl Store {
    pub fn open(db_path: &Path) -> Result<Self, SandboxError> {
        if let Some(parent) = db_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let conn = Connection::open(db_path).map_err(sqlite_err)?;
        conn.execute_batch(SCHEMA).map_err(sqlite_err)?;
        Ok(Self {
            conn,
            db_path: db_path.to_path_buf(),
        })
    }

    pub fn upsert_repository(&self, root: &Path) -> Result<i64, SandboxError> {
        let root_s = root
            .canonicalize()
            .unwrap_or_else(|_| root.to_path_buf())
            .to_string_lossy()
            .to_string();
        let name = root
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("repo")
            .to_string();
        self.conn
            .execute(
                "INSERT INTO repositories(root_path, name) VALUES (?1, ?2)
                 ON CONFLICT(root_path) DO UPDATE SET name=excluded.name",
                params![root_s, name],
            )
            .map_err(sqlite_err)?;
        let id: i64 = self
            .conn
            .query_row(
                "SELECT id FROM repositories WHERE root_path = ?1",
                params![root_s],
                |r| r.get(0),
            )
            .map_err(sqlite_err)?;
        Ok(id)
    }

    pub fn file_hashes(&self, repo_id: i64) -> Result<HashMap<String, String>, SandboxError> {
        let mut stmt = self
            .conn
            .prepare("SELECT path, content_hash FROM files WHERE repo_id = ?1")
            .map_err(sqlite_err)?;
        let rows = stmt
            .query_map(params![repo_id], |r| {
                Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?))
            })
            .map_err(sqlite_err)?;
        let mut out = HashMap::new();
        for row in rows {
            let (p, h) = row.map_err(sqlite_err)?;
            out.insert(p, h);
        }
        Ok(out)
    }

    pub fn delete_files_not_in(
        &self,
        repo_id: i64,
        keep_paths: &HashSet<String>,
    ) -> Result<usize, SandboxError> {
        let mut stmt = self
            .conn
            .prepare("SELECT id, path FROM files WHERE repo_id = ?1")
            .map_err(sqlite_err)?;
        let rows: Vec<(i64, String)> = stmt
            .query_map(params![repo_id], |r| Ok((r.get(0)?, r.get(1)?)))
            .map_err(sqlite_err)?
            .collect::<Result<_, _>>()
            .map_err(sqlite_err)?;
        let mut removed = 0usize;
        for (id, path) in rows {
            if keep_paths.contains(&path) {
                continue;
            }
            self.conn
                .execute("DELETE FROM symbols WHERE file_id = ?1", params![id])
                .map_err(sqlite_err)?;
            self.conn
                .execute("DELETE FROM files WHERE id = ?1", params![id])
                .map_err(sqlite_err)?;
            removed += 1;
        }
        Ok(removed)
    }

    pub fn upsert_file_symbols(
        &self,
        repo_id: i64,
        rel_path: &str,
        content_hash: &str,
        symbols: &[Symbol],
    ) -> Result<(), SandboxError> {
        let existing: Option<i64> = self
            .conn
            .query_row(
                "SELECT id FROM files WHERE repo_id = ?1 AND path = ?2",
                params![repo_id, rel_path],
                |r| r.get(0),
            )
            .optional()
            .map_err(sqlite_err)?;
        let file_id = if let Some(id) = existing {
            self.conn
                .execute(
                    "UPDATE files SET content_hash = ?1 WHERE id = ?2",
                    params![content_hash, id],
                )
                .map_err(sqlite_err)?;
            self.conn
                .execute("DELETE FROM symbols WHERE file_id = ?1", params![id])
                .map_err(sqlite_err)?;
            id
        } else {
            self.conn
                .execute(
                    "INSERT INTO files(repo_id, path, content_hash) VALUES (?1, ?2, ?3)",
                    params![repo_id, rel_path, content_hash],
                )
                .map_err(sqlite_err)?;
            self.conn.last_insert_rowid()
        };
        for sym in symbols {
            self.conn
                .execute(
                    "INSERT INTO symbols(file_id, name, kind, start_line, end_line) VALUES (?1, ?2, ?3, ?4, ?5)",
                    params![file_id, sym.name, sym.kind, sym.start_line as i64, sym.end_line as i64],
                )
                .map_err(sqlite_err)?;
        }
        Ok(())
    }

    pub fn replace_relations(&self, repo_id: i64, relations: &[Relation]) -> Result<usize, SandboxError> {
        self.conn
            .execute("DELETE FROM relations WHERE repo_id = ?1", params![repo_id])
            .map_err(sqlite_err)?;
        for edge in relations {
            self.conn
                .execute(
                    "INSERT INTO relations(repo_id, source, target, relation_type, status, start_line) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                    params![
                        repo_id,
                        edge.source,
                        edge.target,
                        edge.relation_type,
                        edge.status,
                        edge.start_line.map(|n| n as i64),
                    ],
                )
                .map_err(sqlite_err)?;
        }
        Ok(relations.len())
    }

    pub fn rebuild_fts(&self, repo_id: i64) -> Result<(), SandboxError> {
        self.conn
            .execute_batch("DROP TABLE IF EXISTS symbols_fts; CREATE VIRTUAL TABLE symbols_fts USING fts5(name, path, kind, tokenize='porter');")
            .map_err(sqlite_err)?;
        let mut stmt = self
            .conn
            .prepare(
                "SELECT s.name, s.kind, f.path FROM symbols s JOIN files f ON f.id = s.file_id WHERE f.repo_id = ?1",
            )
            .map_err(sqlite_err)?;
        let rows = stmt
            .query_map(params![repo_id], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                ))
            })
            .map_err(sqlite_err)?;
        for row in rows {
            let (name, kind, path) = row.map_err(sqlite_err)?;
            self.conn
                .execute(
                    "INSERT INTO symbols_fts(name, path, kind) VALUES (?1, ?2, ?3)",
                    params![name, path, kind],
                )
                .map_err(sqlite_err)?;
        }
        Ok(())
    }

    pub fn insert_index_snapshot(
        &self,
        repo_id: i64,
        files: i64,
        symbols: i64,
        relations: i64,
        updated_files: i64,
        skipped_unchanged: i64,
        removed_files: i64,
        mode: &str,
    ) -> Result<(), SandboxError> {
        let captured = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
        self.conn
            .execute(
                "INSERT INTO index_snapshots(repo_id, captured_at, files, symbols, relations, updated_files, skipped_unchanged, removed_files, mode)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
                params![
                    repo_id,
                    captured,
                    files,
                    symbols,
                    relations,
                    updated_files,
                    skipped_unchanged,
                    removed_files,
                    mode
                ],
            )
            .map_err(sqlite_err)?;
        Ok(())
    }

    pub fn file_count(&self, repo_id: i64) -> Result<i64, SandboxError> {
        self.conn
            .query_row(
                "SELECT COUNT(*) FROM files WHERE repo_id = ?1",
                params![repo_id],
                |r| r.get(0),
            )
            .map_err(sqlite_err)
    }

    pub fn symbol_count(&self, repo_id: i64) -> Result<i64, SandboxError> {
        self.conn
            .query_row(
                "SELECT COUNT(*) FROM symbols s JOIN files f ON f.id = s.file_id WHERE f.repo_id = ?1",
                params![repo_id],
                |r| r.get(0),
            )
            .map_err(sqlite_err)
    }

    /// Search symbols via FTS5 with LIKE fallback (matches Python Store.search).
    pub fn search(&self, query: &str, limit: usize) -> Result<Vec<SearchHit>, SandboxError> {
        let limit = limit.max(1) as i64;
        let mut fts_query = query.trim().replace('"', "");
        if fts_query.chars().any(|ch| matches!(ch, '.' | '-' | '_' | '/')) {
            fts_query = format!("\"{fts_query}\"");
        }
        let mut out: Vec<SearchHit> = Vec::new();
        let mut seen = HashSet::new();
        if !fts_query.is_empty() {
            let mut stmt = self
                .conn
                .prepare("SELECT name, path FROM symbols_fts WHERE symbols_fts MATCH ?1 LIMIT ?2")
                .map_err(sqlite_err)?;
            let fts_rows: Result<Vec<(String, String)>, _> = stmt
                .query_map(params![fts_query, limit], |r| Ok((r.get(0)?, r.get(1)?)))
                .map_err(sqlite_err)?
                .collect();
            if let Ok(rows) = fts_rows {
                for (name, path) in rows {
                    let mut detail = self
                        .conn
                        .prepare(
                            "SELECT s.name, s.kind, s.start_line, s.end_line, f.path AS file_path \
                             FROM symbols s JOIN files f ON f.id = s.file_id \
                             WHERE s.name = ?1 AND f.path = ?2",
                        )
                        .map_err(sqlite_err)?;
                    let hits = detail
                        .query_map(params![name, path], |r| {
                            Ok(SearchHit {
                                name: r.get(0)?,
                                kind: r.get(1)?,
                                start_line: r.get::<_, i64>(2)? as usize,
                                end_line: r.get::<_, i64>(3)? as usize,
                                file_path: r.get(4)?,
                            })
                        })
                        .map_err(sqlite_err)?;
                    for hit in hits {
                        let hit = hit.map_err(sqlite_err)?;
                        let key = (hit.name.clone(), hit.file_path.clone(), hit.start_line);
                        if seen.insert(key) {
                            out.push(hit);
                        }
                    }
                    if out.len() >= limit as usize {
                        return Ok(out.into_iter().take(limit as usize).collect());
                    }
                }
            }
        }
        let like = format!("%{query}%");
        let mut stmt = self
            .conn
            .prepare(
                "SELECT s.name, s.kind, s.start_line, s.end_line, f.path AS file_path \
                 FROM symbols s JOIN files f ON f.id = s.file_id \
                 WHERE s.name LIKE ?1 OR f.path LIKE ?2 \
                 ORDER BY s.name LIMIT ?3",
            )
            .map_err(sqlite_err)?;
        let rows = stmt
            .query_map(params![like, like, limit.max(50)], |r| {
                Ok(SearchHit {
                    name: r.get(0)?,
                    kind: r.get(1)?,
                    start_line: r.get::<_, i64>(2)? as usize,
                    end_line: r.get::<_, i64>(3)? as usize,
                    file_path: r.get(4)?,
                })
            })
            .map_err(sqlite_err)?;
        for row in rows {
            let hit = row.map_err(sqlite_err)?;
            let key = (hit.name.clone(), hit.file_path.clone(), hit.start_line);
            if seen.insert(key) {
                out.push(hit);
            }
        }
        Ok(out.into_iter().take(limit as usize).collect())
    }
}

#[derive(Debug, Clone, serde::Serialize, PartialEq, Eq)]
pub struct SearchHit {
    pub name: String,
    pub kind: String,
    pub start_line: usize,
    pub end_line: usize,
    pub file_path: String,
}

fn sqlite_err(err: rusqlite::Error) -> SandboxError {
    SandboxError::Io(std::io::Error::other(err.to_string()))
}
