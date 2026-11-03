use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use serde::Serialize;
use walkdir::WalkDir;

use crate::sandbox::{assert_path_in_root, is_sensitive_path, SandboxError};

const SKIP_DIRS: &[&str] = &[
    ".git",
    ".hg",
    ".svn",
    ".witnis",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "target",
];

const SKIP_SUFFIXES: &[&str] = &[".pyc", ".pyo", ".so", ".dll", ".exe"];

const SOURCE_SUFFIXES: &[&str] = &[
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".java",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SourceFile {
    pub path: PathBuf,
    pub rel_path: String,
}

/// Walk `root` and return sorted source files (Python parity with `discover.py`).
pub fn iter_source_files(root: &Path) -> Result<Vec<SourceFile>, SandboxError> {
    let root = root.canonicalize().unwrap_or_else(|_| root.to_path_buf());
    if !root.is_dir() {
        return Err(SandboxError::Io(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Not a directory: {}", root.display()),
        )));
    }

    let mut found: BTreeSet<(String, PathBuf)> = BTreeSet::new();
    for entry in WalkDir::new(&root)
        .into_iter()
        .filter_entry(|e| {
            if e.file_type().is_dir() {
                let name = e.file_name().to_string_lossy();
                return !SKIP_DIRS.iter().any(|s| *s == name);
            }
            true
        })
        .filter_map(|e| e.ok())
    {
        if !entry.file_type().is_file() {
            continue;
        }
        let path = entry.path();
        if assert_path_in_root(&root, path).is_err() {
            continue;
        }
        if is_sensitive_path(path) {
            continue;
        }
        let name = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
        if SKIP_SUFFIXES.iter().any(|s| name.ends_with(s)) {
            continue;
        }
        let Some(ext) = path.extension().map(|e| format!(".{}", e.to_string_lossy().to_ascii_lowercase())) else {
            continue;
        };
        if !SOURCE_SUFFIXES.iter().any(|s| *s == ext) {
            continue;
        }
        let rel = path
            .strip_prefix(&root)
            .unwrap_or(path)
            .to_string_lossy()
            .replace('\\', "/");
        found.insert((rel.clone(), path.to_path_buf()));
    }

    Ok(found
        .into_iter()
        .map(|(rel_path, path)| SourceFile { path, rel_path })
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn finds_py_and_skips_venv() {
        let dir = tempdir().unwrap();
        fs::create_dir_all(dir.path().join("pkg")).unwrap();
        fs::create_dir_all(dir.path().join(".venv").join("lib")).unwrap();
        fs::write(dir.path().join("pkg/a.py"), b"x").unwrap();
        fs::write(dir.path().join(".venv/lib/b.py"), b"y").unwrap();
        fs::write(dir.path().join(".env"), b"SECRET=1").unwrap();
        let files = iter_source_files(dir.path()).unwrap();
        let rels: Vec<_> = files.iter().map(|f| f.rel_path.as_str()).collect();
        assert_eq!(rels, vec!["pkg/a.py"]);
    }
}
