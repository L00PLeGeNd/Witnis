use pyo3::exceptions::{PyIOError, PyPermissionError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::path::PathBuf;

use witnis_core::parse::{go, java, js, python};
use witnis_core::{
    assert_path_in_root, index_repository, is_sensitive_path, iter_source_files,
    scan_source_digests, search_symbols, sha256_file, SandboxError,
};

fn map_err(err: SandboxError) -> PyErr {
    match err {
        SandboxError::EscapesRoot { .. } => PyPermissionError::new_err(err.to_string()),
        SandboxError::Io(e) => PyIOError::new_err(e.to_string()),
    }
}

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

#[pyfunction]
fn scan_digests(py: Python<'_>, root: &str) -> PyResult<Py<PyList>> {
    let rows = scan_source_digests(&PathBuf::from(root)).map_err(map_err)?;
    let list = PyList::empty(py);
    for row in rows {
        let d = PyDict::new(py);
        d.set_item("rel_path", row.rel_path)?;
        d.set_item("sha256", row.sha256)?;
        d.set_item("path", row.path.to_string_lossy().to_string())?;
        list.append(d)?;
    }
    Ok(list.into())
}

fn symbols_to_py(py: Python<'_>, symbols: Vec<witnis_core::Symbol>) -> PyResult<Py<PyList>> {
    let list = PyList::empty(py);
    for s in symbols {
        let d = PyDict::new(py);
        d.set_item("name", s.name)?;
        d.set_item("kind", s.kind)?;
        d.set_item("file_path", s.file_path)?;
        d.set_item("start_line", s.start_line)?;
        d.set_item("end_line", s.end_line)?;
        list.append(d)?;
    }
    Ok(list.into())
}

fn relations_to_py(py: Python<'_>, edges: Vec<witnis_core::Relation>) -> PyResult<Py<PyList>> {
    let list = PyList::empty(py);
    for e in edges {
        let d = PyDict::new(py);
        d.set_item("source", e.source)?;
        d.set_item("target", e.target)?;
        d.set_item("relation_type", e.relation_type)?;
        d.set_item("status", e.status)?;
        d.set_item("start_line", e.start_line)?;
        list.append(d)?;
    }
    Ok(list.into())
}

#[pyfunction]
fn parse_shallow(
    py: Python<'_>,
    lang: &str,
    source: &str,
    rel_path: &str,
) -> PyResult<(Py<PyList>, Py<PyList>)> {
    let (symbols, relations) = match lang {
        "go" => {
            let mut edges = go::parse_imports(source, rel_path);
            edges.extend(go::parse_calls(source, rel_path));
            (go::parse_symbols(source, rel_path), edges)
        }
        "java" => (
            java::parse_symbols(source, rel_path),
            java::parse_relations(source, rel_path),
        ),
        "js" | "ts" => {
            let mut edges = js::parse_imports(source, rel_path);
            edges.extend(js::parse_calls(source, rel_path));
            (js::parse_symbols(source, rel_path), edges)
        }
        "python" | "py" => (
            python::parse_symbols(source, rel_path),
            python::parse_relations(source, rel_path),
        ),
        other => {
            return Err(PyValueError::new_err(format!(
                "unsupported shallow lang: {other}"
            )))
        }
    };
    Ok((symbols_to_py(py, symbols)?, relations_to_py(py, relations)?))
}

#[pyfunction]
fn index_repo(
    py: Python<'_>,
    root: &str,
    db_path: &str,
    incremental: bool,
) -> PyResult<Py<PyDict>> {
    let stats = index_repository(
        &PathBuf::from(root),
        &PathBuf::from(db_path),
        incremental,
    )
    .map_err(map_err)?;
    let d = PyDict::new(py);
    d.set_item("repository", stats.repository)?;
    d.set_item("files", stats.files)?;
    d.set_item("symbols", stats.symbols)?;
    d.set_item("db_path", stats.db_path)?;
    d.set_item("updated_files", stats.updated_files)?;
    d.set_item("skipped_unchanged", stats.skipped_unchanged)?;
    d.set_item("removed_files", stats.removed_files)?;
    d.set_item("relations", stats.relations)?;
    d.set_item("mode", stats.mode)?;
    d.set_item("backend", stats.backend)?;
    Ok(d.into())
}

#[pyfunction]
fn search_db(py: Python<'_>, db_path: &str, query: &str, limit: usize) -> PyResult<Py<PyList>> {
    let hits = search_symbols(&PathBuf::from(db_path), query, limit).map_err(map_err)?;
    let list = PyList::empty(py);
    for h in hits {
        let d = PyDict::new(py);
        d.set_item("name", h.name)?;
        d.set_item("kind", h.kind)?;
        d.set_item("start_line", h.start_line)?;
        d.set_item("end_line", h.end_line)?;
        d.set_item("file_path", h.file_path)?;
        list.append(d)?;
    }
    Ok(list.into())
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(list_source_files, m)?)?;
    m.add_function(wrap_pyfunction!(file_sha256, m)?)?;
    m.add_function(wrap_pyfunction!(path_is_sensitive, m)?)?;
    m.add_function(wrap_pyfunction!(ensure_in_root, m)?)?;
    m.add_function(wrap_pyfunction!(scan_digests, m)?)?;
    m.add_function(wrap_pyfunction!(parse_shallow, m)?)?;
    m.add_function(wrap_pyfunction!(index_repo, m)?)?;
    m.add_function(wrap_pyfunction!(search_db, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
