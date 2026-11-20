use std::path::{Path, PathBuf};

use serde::Serialize;

use crate::discover::iter_source_files;
use crate::hash::sha256_file;
use crate::sandbox::SandboxError;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FileDigest {
    pub rel_path: String,
    pub path: PathBuf,
    pub sha256: String,
}

/// Discover source files under `root` and compute SHA-256 digests.
pub fn scan_source_digests(root: &Path) -> Result<Vec<FileDigest>, SandboxError> {
    let files = iter_source_files(root)?;
    let mut out = Vec::with_capacity(files.len());
    for f in files {
        let sha256 = sha256_file(&f.path)?;
        out.push(FileDigest {
            rel_path: f.rel_path,
            path: f.path,
            sha256,
        });
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn digests_python_file() {
        let dir = tempdir().unwrap();
        fs::write(dir.path().join("a.py"), b"hello").unwrap();
        let rows = scan_source_digests(dir.path()).unwrap();
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].rel_path, "a.py");
        assert_eq!(
            rows[0].sha256,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        );
    }
}
