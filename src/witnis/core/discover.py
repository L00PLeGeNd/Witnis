from __future__ import annotations

import os
from pathlib import Path

from witnis.core.native import rust_list_source_files
from witnis.core.security import assert_path_in_root, is_sensitive_path

SKIP_DIR_NAMES = {
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
}

SKIP_FILE_SUFFIXES = {".pyc", ".pyo", ".so", ".dll", ".exe"}

SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".java",
}


def iter_source_files(root: Path) -> list[Path]:
    root = root.resolve()
    # Prefer Rust discover when witnis._native is built.
    rust_rels = rust_list_source_files(root)
    if rust_rels is not None:
        return [root / rel for rel in rust_rels]

    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                assert_path_in_root(root, path)
            except PermissionError:
                continue
            if is_sensitive_path(path):
                continue
            if path.suffix in SKIP_FILE_SUFFIXES:
                continue
            if path.suffix in SOURCE_SUFFIXES:
                found.append(path)
    return sorted(found)
