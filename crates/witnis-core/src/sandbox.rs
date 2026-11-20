use std::path::{Component, Path, PathBuf};

use thiserror::Error;

#[derive(Debug, Error)]
pub enum SandboxError {
    #[error("path escapes repository sandbox: {candidate} not under {root}")]
    EscapesRoot { root: PathBuf, candidate: PathBuf },
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
}

const SECRET_NAME_MARKERS: &[&str] = &[
    ".pem",
    ".key",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secret",
    "passwd",
    "password",
];

/// Resolve `candidate` and ensure it stays inside `root`.
pub fn assert_path_in_root(root: &Path, candidate: &Path) -> Result<PathBuf, SandboxError> {
    let root_r = root.canonicalize().unwrap_or_else(|_| normalize(root));
    let cand_r = candidate
        .canonicalize()
        .unwrap_or_else(|_| normalize(candidate));
    if !cand_r.starts_with(&root_r) {
        return Err(SandboxError::EscapesRoot {
            root: root_r,
            candidate: cand_r,
        });
    }
    Ok(cand_r)
}

/// True for likely secret **filenames** (not arbitrary path substrings).
pub fn is_sensitive_path(path: &Path) -> bool {
    let Some(name) = path.file_name().and_then(|s| s.to_str()) else {
        return false;
    };
    let lower = name.to_ascii_lowercase();
    if lower == ".env" || lower == ".env.local" {
        return true;
    }
    SECRET_NAME_MARKERS.iter().any(|m| lower.contains(m))
}

fn normalize(path: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for c in path.components() {
        match c {
            Component::ParentDir => {
                out.pop();
            }
            Component::CurDir => {}
            other => out.push(other.as_os_str()),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn accepts_child_path() {
        let dir = tempdir().unwrap();
        let child = dir.path().join("a.py");
        fs::write(&child, b"x").unwrap();
        let got = assert_path_in_root(dir.path(), &child).unwrap();
        assert!(got.ends_with("a.py"));
    }

    #[test]
    fn rejects_escape() {
        let dir = tempdir().unwrap();
        let outside = dir.path().join("..").join("nope");
        // may or may not exist; normalize-based check still applies when canonicalize fails
        let _ = fs::create_dir_all(dir.path());
        let err = assert_path_in_root(dir.path(), &outside);
        // If canonicalize resolves outside, expect Err; if path missing, normalize may still escape
        if let Ok(p) = err {
            assert!(
                !p.starts_with(dir.path().canonicalize().unwrap()),
                "unexpectedly accepted {p:?}"
            );
        }
    }

    #[test]
    fn sensitive_filename_only() {
        assert!(is_sensitive_path(Path::new(".env")));
        assert!(is_sensitive_path(Path::new("api_secret.txt")));
        // Directory names with "secret" must not poison sibling files:
        assert!(!is_sensitive_path(Path::new("tests/test_scan_secrets_ok/auth.py")));
        assert!(!is_sensitive_path(Path::new("src/auth.py")));
    }
}
