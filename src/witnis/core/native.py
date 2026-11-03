"""Optional Rust native acceleration (witnis._native via PyO3).

Falls back silently when the extension is not built.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

_list_source_files: Callable[[str], list[str]] | None
_file_sha256: Callable[[str], str] | None
_scan_digests: Callable[[str], list[dict[str, Any]]] | None
_parse_shallow: Callable[[str, str, str], tuple[list[dict], list[dict]]] | None

try:
    from witnis import _native as _ext

    _list_source_files = _ext.list_source_files
    _file_sha256 = _ext.file_sha256
    _scan_digests = _ext.scan_digests
    _parse_shallow = _ext.parse_shallow
    NATIVE_AVAILABLE = True
    NATIVE_VERSION = getattr(_ext, "__version__", "unknown")
except Exception:  # pragma: no cover - missing extension is normal
    _list_source_files = None
    _file_sha256 = None
    _scan_digests = None
    _parse_shallow = None
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
