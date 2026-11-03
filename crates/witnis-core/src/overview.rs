use std::path::Path;

use serde::Serialize;

use crate::sandbox::SandboxError;
use crate::store::Store;

#[derive(Debug, Clone, Serialize)]
pub struct Overview {
    pub repository: Option<String>,
    pub root_path: Option<String>,
    pub files: i64,
    pub symbols: i64,
    pub relations: i64,
    pub db_path: String,
}

/// Summarize an indexed Witnis SQLite database.
pub fn overview_db(db_path: &Path) -> Result<Overview, SandboxError> {
    let store = Store::open(db_path)?;
    let meta = store.latest_repo_meta()?;
    let (files, symbols, relations) = if let Some((_, _, id)) = &meta {
        (
            store.file_count(*id)?,
            store.symbol_count(*id)?,
            store.relation_count(*id)?,
        )
    } else {
        (0, 0, 0)
    };
    Ok(Overview {
        repository: meta.as_ref().map(|(name, _, _)| name.clone()),
        root_path: meta.as_ref().map(|(_, root, _)| root.clone()),
        files,
        symbols,
        relations,
        db_path: db_path.display().to_string(),
    })
}
