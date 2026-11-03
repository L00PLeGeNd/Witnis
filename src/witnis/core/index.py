from __future__ import annotations

import hashlib
from pathlib import Path

from witnis.core.calls_python import parse_python_calls
from witnis.core.discover import iter_source_files
from witnis.core.models import IndexStats, Symbol
from witnis.core.parse_go import parse_go_file
from witnis.core.parse_java import parse_java_file
from witnis.core.parse_js import parse_js_file
from witnis.core.parse_python import parse_python_file
from witnis.core.references_python import parse_python_references
from witnis.core.relations_go import parse_go_calls, parse_go_imports
from witnis.core.relations_java import parse_java_calls, parse_java_imports
from witnis.core.relations_js import parse_js_calls, parse_js_imports
from witnis.core.relations_python import (
    parse_python_decorators,
    parse_python_imports,
    parse_python_inheritance,
    parse_python_overrides,
)
from witnis.core.store import Store

_JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def _parse_symbols(path: Path, *, rel_path: str) -> list[Symbol]:
    if path.suffix == ".py":
        return parse_python_file(path, rel_path=rel_path)
    if path.suffix in _JS_SUFFIXES:
        return parse_js_file(path, rel_path=rel_path)
    if path.suffix == ".go":
        return parse_go_file(path, rel_path=rel_path)
    if path.suffix == ".java":
        return parse_java_file(path, rel_path=rel_path)
    return []


def _parse_relations(path: Path, *, rel_path: str) -> list[dict]:
    if path.suffix == ".py":
        edges: list[dict] = []
        edges.extend(parse_python_imports(path, rel_path=rel_path))
        edges.extend(parse_python_calls(path, rel_path=rel_path))
        edges.extend(parse_python_references(path, rel_path=rel_path))
        edges.extend(parse_python_inheritance(path, rel_path=rel_path))
        edges.extend(parse_python_decorators(path, rel_path=rel_path))
        edges.extend(parse_python_overrides(path, rel_path=rel_path))
        return edges
    if path.suffix in _JS_SUFFIXES:
        return parse_js_imports(path, rel_path=rel_path) + parse_js_calls(
            path, rel_path=rel_path
        )
    if path.suffix == ".go":
        return parse_go_imports(path, rel_path=rel_path) + parse_go_calls(
            path, rel_path=rel_path
        )
    if path.suffix == ".java":
        return parse_java_imports(path, rel_path=rel_path) + parse_java_calls(
            path, rel_path=rel_path
        )
    return []


def index_repository(
    root: Path, db_path: Path, *, incremental: bool = True
) -> IndexStats:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")

    store = Store(db_path)
    try:
        repo_id = store.upsert_repository(root)
        paths = iter_source_files(root)
        relations: list[dict] = []
        for path in paths:
            rel = path.relative_to(root).as_posix()
            relations.extend(_parse_relations(path, rel_path=rel))

        if not incremental:
            payload = []
            for path in paths:
                rel = path.relative_to(root).as_posix()
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                symbols = _parse_symbols(path, rel_path=rel)
                payload.append((rel, digest, symbols))
            files, symbols, rel_count = store.replace_repo_contents(
                repo_id, payload, relations=relations
            )
            store.rebuild_fts(repo_id)
            store.insert_index_snapshot(
                repo_id,
                files=files,
                symbols=symbols,
                relations=rel_count,
                updated_files=files,
                skipped_unchanged=0,
                removed_files=0,
                mode="full",
            )
            return IndexStats(
                repository=root.name,
                files=files,
                symbols=symbols,
                db_path=str(db_path.resolve()),
                updated_files=files,
                skipped_unchanged=0,
                removed_files=0,
            )

        existing = store.file_hashes(repo_id)
        keep_paths: set[str] = set()
        updated = 0
        skipped = 0
        for path in paths:
            rel = path.relative_to(root).as_posix()
            keep_paths.add(rel)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if existing.get(rel) == digest:
                skipped += 1
                continue
            symbols = _parse_symbols(path, rel_path=rel)
            store.upsert_file_symbols(repo_id, rel, digest, symbols)
            updated += 1

        removed = store.delete_files_not_in(repo_id, keep_paths)
        rel_count = store.replace_relations(repo_id, relations)
        store.rebuild_fts(repo_id)
        files = store.file_count(repo_id)
        symbols = store.symbol_count(repo_id)
        store.insert_index_snapshot(
            repo_id,
            files=files,
            symbols=symbols,
            relations=rel_count,
            updated_files=updated,
            skipped_unchanged=skipped,
            removed_files=removed,
            mode="incremental",
        )
        return IndexStats(
            repository=root.name,
            files=files,
            symbols=symbols,
            db_path=str(db_path.resolve()),
            updated_files=updated,
            skipped_unchanged=skipped,
            removed_files=removed,
        )
    finally:
        store.close()
