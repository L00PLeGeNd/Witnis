"""Optional Rust native acceleration (witnis._native via PyO3).

Falls back silently when the extension is not built.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

_list_source_files: Callable[[str], list[str]] | None
_file_sha256: Callable[[str], str] | None
_path_is_sensitive: Callable[[str], bool] | None
_ensure_in_root: Callable[[str, str], str] | None

try:
    from witnis import _native as _ext

    _list_source_files = _ext.list_source_files
    _file_sha256 = _ext.file_sha256
    _path_is_sensitive = _ext.path_is_sensitive
    _ensure_in_root = _ext.ensure_in_root
    NATIVE_AVAILABLE = True
    NATIVE_VERSION = getattr(_ext, "__version__", "unknown")
except Exception:  # pragma: no cover - missing extension is normal
    _list_source_files = None
    _file_sha256 = None
    _path_is_sensitive = None
    _ensure_in_root = None
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
