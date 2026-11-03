"""Optional Rust native acceleration (witnis._native via PyO3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

_list_source_files: Callable[[str], list[str]] | None
_file_sha256: Callable[[str], str] | None
_scan_digests: Callable[[str], list[dict[str, Any]]] | None
_parse_shallow: Callable[[str, str, str], tuple[list[dict], list[dict]]] | None
_index_repo: Callable[[str, str, bool], dict[str, Any]] | None
_search_db: Callable[[str, str, int], list[dict[str, Any]]] | None

try:
    from witnis import _native as _ext

    _list_source_files = _ext.list_source_files
    _file_sha256 = _ext.file_sha256
    _scan_digests = _ext.scan_digests
    _parse_shallow = _ext.parse_shallow
    _index_repo = _ext.index_repo
    _search_db = getattr(_ext, "search_db", None)
    NATIVE_AVAILABLE = True
    NATIVE_VERSION = getattr(_ext, "__version__", "unknown")
except Exception:  # pragma: no cover
    _list_source_files = None
    _file_sha256 = None
    _scan_digests = None
    _parse_shallow = None
    _index_repo = None
    _search_db = None
    NATIVE_AVAILABLE = False
    NATIVE_VERSION = None


def rust_list_source_files(root: Path) -> list[str] | None:
    if _list_source_files is None:
        return None
    return list(_list_source_files(str(root.resolve())))


def rust_file_sha256(path: Path) -> str | None:
    if _file_sha256 is None:
        return None
    return str(_file_sha256(str(path)))


def rust_scan_digests(root: Path) -> list[dict[str, Any]] | None:
    if _scan_digests is None:
        return None
    return list(_scan_digests(str(root.resolve())))


def rust_parse_shallow(
    lang: str, source: str, rel_path: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    if _parse_shallow is None:
        return None
    symbols, relations = _parse_shallow(lang, source, rel_path)
    return list(symbols), list(relations)


def rust_index_repository(
    root: Path, db_path: Path, *, incremental: bool = True
) -> dict[str, Any] | None:
    if _index_repo is None:
        return None
    return dict(
        _index_repo(str(root.resolve()), str(Path(db_path).resolve()), incremental)
    )


def rust_search(
    db_path: Path, query: str, *, limit: int = 50
) -> list[dict[str, Any]] | None:
    if _search_db is None:
        return None
    return list(_search_db(str(Path(db_path).resolve()), query, int(limit)))
