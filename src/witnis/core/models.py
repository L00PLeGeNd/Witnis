from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class IndexStats:
    repository: str
    files: int
    symbols: int
    db_path: str
    updated_files: int = 0
    skipped_unchanged: int = 0
    removed_files: int = 0
