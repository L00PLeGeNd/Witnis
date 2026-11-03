use pyo3::exceptions::{PyIOError, PyPermissionError};
use pyo3::prelude::*;
use std::path::PathBuf;

use witnis_core::{assert_path_in_root, is_sensitive_path, iter_source_files, sha256_file, SandboxError};

fn map_err(err: SandboxError) -> PyErr {
    match err {
        SandboxError::EscapesRoot { .. } => PyPermissionError::new_err(err.to_string()),
        SandboxError::Io(e) => PyIOError::new_err(e.to_string()),
    }
}

/// List relative source paths under root (sorted).
#[pyfunction]
fn list_source_files(root: &str) -> PyResult<Vec<String>> {
    let files = iter_source_files(&PathBuf::from(root)).map_err(map_err)?;
    Ok(files.into_iter().map(|f| f.rel_path).collect())
}

#[pyfunction]
fn file_sha256(path: &str) -> PyResult<String> {
    sha256_file(&PathBuf::from(path)).map_err(map_err)
}

#[pyfunction]
fn path_is_sensitive(path: &str) -> bool {
    is_sensitive_path(&PathBuf::from(path))
}

#[pyfunction]
fn ensure_in_root(root: &str, candidate: &str) -> PyResult<String> {
    let p = assert_path_in_root(&PathBuf::from(root), &PathBuf::from(candidate)).map_err(map_err)?;
    Ok(p.to_string_lossy().into_owned())
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(list_source_files, m)?)?;
    m.add_function(wrap_pyfunction!(file_sha256, m)?)?;
    m.add_function(wrap_pyfunction!(path_is_sensitive, m)?)?;
    m.add_function(wrap_pyfunction!(ensure_in_root, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
