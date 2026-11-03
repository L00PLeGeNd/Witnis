from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from witnis.core.models import Symbol

SCHEMA = """
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    UNIQUE(repo_id, path),
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    start_line INTEGER,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target);

CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    hash TEXT NOT NULL,
    author_name TEXT,
    author_email TEXT,
    committed_at TEXT,
    subject TEXT,
    UNIQUE(repo_id, hash),
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS commit_files (
    id INTEGER PRIMARY KEY,
    commit_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    change_status TEXT,
    FOREIGN KEY(commit_id) REFERENCES commits(id)
);

CREATE TABLE IF NOT EXISTS index_snapshots (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    files INTEGER NOT NULL,
    symbols INTEGER NOT NULL,
    relations INTEGER NOT NULL,
    updated_files INTEGER,
    skipped_unchanged INTEGER,
    removed_files INTEGER,
    mode TEXT,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS verification_runs (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    plan_id TEXT,
    target TEXT,
    revision TEXT,
    state TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    report_json TEXT NOT NULL,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    run_id INTEGER,
    source_type TEXT NOT NULL,
    source_ref TEXT,
    path TEXT,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(repo_id) REFERENCES repositories(id),
    FOREIGN KEY(run_id) REFERENCES verification_runs(id)
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    run_id INTEGER,
    step_id TEXT,
    status TEXT NOT NULL,
    exit_code INTEGER,
    stdout_tail TEXT,
    stderr_tail TEXT,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(repo_id) REFERENCES repositories(id),
    FOREIGN KEY(run_id) REFERENCES verification_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence_items(status);
CREATE INDEX IF NOT EXISTS idx_evidence_ref ON evidence_items(source_ref);

CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    name,
    path,
    kind,
    tokenize='porter'
);
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def upsert_repository(self, root: Path) -> int:
        root_s = str(root.resolve())
        name = root.name
        self.conn.execute(
            "INSERT INTO repositories(root_path, name) VALUES (?, ?) "
            "ON CONFLICT(root_path) DO UPDATE SET name=excluded.name",
            (root_s, name),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM repositories WHERE root_path = ?", (root_s,)
        ).fetchone()
        assert row is not None
        return int(row["id"])

    def file_hashes(self, repo_id: int) -> dict[str, str]:
        rows = self.conn.execute(
            "SELECT path, content_hash FROM files WHERE repo_id = ?", (repo_id,)
        ).fetchall()
        return {str(r["path"]): str(r["content_hash"]) for r in rows}

    def delete_files_not_in(self, repo_id: int, keep_paths: set[str]) -> int:
        rows = self.conn.execute(
            "SELECT id, path FROM files WHERE repo_id = ?", (repo_id,)
        ).fetchall()
        removed = 0
        for row in rows:
            if row["path"] in keep_paths:
                continue
            self.conn.execute("DELETE FROM symbols WHERE file_id = ?", (row["id"],))
            self.conn.execute("DELETE FROM files WHERE id = ?", (row["id"],))
            removed += 1
        self.conn.commit()
        return removed

    def upsert_file_symbols(
        self, repo_id: int, rel_path: str, content_hash: str, symbols: list[Symbol]
    ) -> None:
        existing = self.conn.execute(
            "SELECT id FROM files WHERE repo_id = ? AND path = ?",
            (repo_id, rel_path),
        ).fetchone()
        if existing is None:
            cur = self.conn.execute(
                "INSERT INTO files(repo_id, path, content_hash) VALUES (?, ?, ?)",
                (repo_id, rel_path, content_hash),
            )
            file_id = int(cur.lastrowid)
        else:
            file_id = int(existing["id"])
            self.conn.execute(
                "UPDATE files SET content_hash = ? WHERE id = ?",
                (content_hash, file_id),
            )
            self.conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        for sym in symbols:
            self.conn.execute(
                "INSERT INTO symbols(file_id, name, kind, start_line, end_line) "
                "VALUES (?, ?, ?, ?, ?)",
                (file_id, sym.name, sym.kind, sym.start_line, sym.end_line),
            )
        self.conn.commit()

    def replace_relations(self, repo_id: int, relations: list[dict]) -> int:
        self.conn.execute("DELETE FROM relations WHERE repo_id = ?", (repo_id,))
        for edge in relations:
            self.conn.execute(
                "INSERT INTO relations(repo_id, source, target, relation_type, status, start_line) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    repo_id,
                    edge["source"],
                    edge["target"],
                    edge["relation_type"],
                    edge["status"],
                    edge.get("start_line"),
                ),
            )
        self.conn.commit()
        return len(relations)

    def append_relations(self, repo_id: int, relations: list[dict]) -> int:
        """Insert relation edges without wiping existing rows; skip exact duplicates."""
        added = 0
        for edge in relations:
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            relation_type = str(edge.get("relation_type") or "calls")
            status = str(edge.get("status") or "observed")
            start_line = edge.get("start_line")
            if not source or not target:
                continue
            exists = self.conn.execute(
                "SELECT 1 FROM relations WHERE repo_id = ? AND source = ? AND target = ? "
                "AND relation_type = ? AND IFNULL(start_line, -1) = IFNULL(?, -1) LIMIT 1",
                (repo_id, source, target, relation_type, start_line),
            ).fetchone()
            if exists:
                continue
            self.conn.execute(
                "INSERT INTO relations(repo_id, source, target, relation_type, status, start_line) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (repo_id, source, target, relation_type, status, start_line),
            )
            added += 1
        self.conn.commit()
        return added

    def rebuild_fts(self, repo_id: int) -> None:
        # Recreate to avoid stale contentless FTS tables from earlier schemas.
        self.conn.execute("DROP TABLE IF EXISTS symbols_fts")
        self.conn.execute(
            "CREATE VIRTUAL TABLE symbols_fts USING fts5("
            "name, path, kind, tokenize='porter')"
        )
        rows = self.conn.execute(
            "SELECT s.name, s.kind, f.path FROM symbols s "
            "JOIN files f ON f.id = s.file_id WHERE f.repo_id = ?",
            (repo_id,),
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "INSERT INTO symbols_fts(name, path, kind) VALUES (?, ?, ?)",
                (row["name"], row["path"], row["kind"]),
            )
        self.conn.commit()

    def symbol_count(self, repo_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM symbols s "
            "JOIN files f ON f.id = s.file_id WHERE f.repo_id = ?",
            (repo_id,),
        ).fetchone()
        return int(row["c"])

    def file_count(self, repo_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM files WHERE repo_id = ?", (repo_id,)
        ).fetchone()
        return int(row["c"])

    def replace_repo_contents(
        self,
        repo_id: int,
        files: list[tuple[str, str, list[Symbol]]],
        relations: list[dict] | None = None,
    ) -> tuple[int, int, int]:
        """Full rebuild (non-incremental). Returns (files, symbols, relations)."""
        self.conn.execute(
            "DELETE FROM symbols WHERE file_id IN (SELECT id FROM files WHERE repo_id = ?)",
            (repo_id,),
        )
        self.conn.execute("DELETE FROM relations WHERE repo_id = ?", (repo_id,))
        self.conn.execute("DELETE FROM files WHERE repo_id = ?", (repo_id,))
        self.conn.commit()
        for rel_path, content_hash, symbols in files:
            self.upsert_file_symbols(repo_id, rel_path, content_hash, symbols)
        rel_count = self.replace_relations(repo_id, relations or [])
        return len(files), self.symbol_count(repo_id), rel_count

    def _latest_repo_id(self) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM repositories ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return int(row["id"]) if row else None

    def list_relations(
        self, repo_id: int | None = None, limit: int = 100
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        rows = self.conn.execute(
            "SELECT source, target, relation_type, status, start_line "
            "FROM relations WHERE repo_id = ? ORDER BY id LIMIT ?",
            (repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_relations(
        self,
        *,
        relation_type: str | None = None,
        source_contains: str | None = None,
        target_equals: str | None = None,
        repo_id: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        clauses = ["repo_id = ?"]
        params: list[object] = [repo_id]
        if relation_type:
            clauses.append("relation_type = ?")
            params.append(relation_type)
        if source_contains:
            clauses.append("source LIKE ?")
            params.append(f"%{source_contains}%")
        if target_equals:
            clauses.append("target = ?")
            params.append(target_equals)
        params.append(limit)
        sql = (
            "SELECT source, target, relation_type, status, start_line FROM relations "
            f"WHERE {' AND '.join(clauses)} ORDER BY id LIMIT ?"
        )
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def overview(self, repo_id: int | None = None) -> dict:
        if repo_id is None:
            row = self.conn.execute(
                "SELECT id, name, root_path FROM repositories ORDER BY id DESC LIMIT 1"
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT id, name, root_path FROM repositories WHERE id = ?", (repo_id,)
            ).fetchone()
        if row is None:
            return {"repository": None, "files": 0, "symbols": 0}
        rid = int(row["id"])
        files = self.conn.execute(
            "SELECT COUNT(*) AS c FROM files WHERE repo_id = ?", (rid,)
        ).fetchone()["c"]
        symbols = self.conn.execute(
            "SELECT COUNT(*) AS c FROM symbols s "
            "JOIN files f ON f.id = s.file_id WHERE f.repo_id = ?",
            (rid,),
        ).fetchone()["c"]
        return {
            "repository": {
                "id": rid,
                "name": row["name"],
                "root_path": row["root_path"],
            },
            "files": int(files),
            "symbols": int(symbols),
        }

    def upsert_commit(
        self,
        repo_id: int,
        meta: dict[str, Any],
        files: list[dict[str, Any]] | None = None,
    ) -> int:
        self.conn.execute(
            "INSERT INTO commits(repo_id, hash, author_name, author_email, committed_at, subject) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(repo_id, hash) DO UPDATE SET "
            "author_name=excluded.author_name, author_email=excluded.author_email, "
            "committed_at=excluded.committed_at, subject=excluded.subject",
            (
                repo_id,
                meta.get("hash"),
                meta.get("author_name"),
                meta.get("author_email"),
                meta.get("committed_at"),
                meta.get("subject"),
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM commits WHERE repo_id = ? AND hash = ?",
            (repo_id, meta.get("hash")),
        ).fetchone()
        assert row is not None
        commit_id = int(row["id"])
        if files is not None:
            self.conn.execute(
                "DELETE FROM commit_files WHERE commit_id = ?", (commit_id,)
            )
            for f in files:
                self.conn.execute(
                    "INSERT INTO commit_files(commit_id, path, change_status) VALUES (?, ?, ?)",
                    (commit_id, f.get("path"), f.get("status")),
                )
            self.conn.commit()
        return commit_id

    def get_commit(self, repo_id: int, commit_hash: str) -> dict | None:
        row = self.conn.execute(
            "SELECT hash, author_name, author_email, committed_at, subject "
            "FROM commits WHERE repo_id = ? AND hash = ?",
            (repo_id, commit_hash),
        ).fetchone()
        return dict(row) if row else None

    def list_commits(self, repo_id: int | None = None, limit: int = 20) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        rows = self.conn.execute(
            "SELECT hash, author_name, author_email, committed_at, subject "
            "FROM commits WHERE repo_id = ? ORDER BY id DESC LIMIT ?",
            (repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_index_snapshot(
        self,
        repo_id: int,
        *,
        files: int,
        symbols: int,
        relations: int,
        updated_files: int | None = None,
        skipped_unchanged: int | None = None,
        removed_files: int | None = None,
        mode: str = "full",
    ) -> int:
        captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = self.conn.execute(
            "INSERT INTO index_snapshots("
            "repo_id, captured_at, files, symbols, relations, "
            "updated_files, skipped_unchanged, removed_files, mode"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                repo_id,
                captured,
                files,
                symbols,
                relations,
                updated_files,
                skipped_unchanged,
                removed_files,
                mode,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_index_snapshots(
        self, repo_id: int | None = None, limit: int = 20
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        rows = self.conn.execute(
            "SELECT id, captured_at, files, symbols, relations, "
            "updated_files, skipped_unchanged, removed_files, mode "
            "FROM index_snapshots WHERE repo_id = ? ORDER BY id DESC LIMIT ?",
            (repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def relation_count(self, repo_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM relations WHERE repo_id = ?", (repo_id,)
        ).fetchone()
        return int(row["c"])

    def insert_verification_run(
        self,
        repo_id: int,
        *,
        plan_id: str | None,
        target: str | None,
        revision: str | None,
        state: str,
        report: dict[str, Any],
    ) -> int:
        captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = self.conn.execute(
            "INSERT INTO verification_runs("
            "repo_id, plan_id, target, revision, state, captured_at, report_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                repo_id,
                plan_id,
                target,
                revision,
                state,
                captured,
                json.dumps(report, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def insert_evidence_items(
        self,
        repo_id: int,
        items: list[dict[str, Any]],
        *,
        run_id: int | None = None,
    ) -> int:
        captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        hashes = self.file_hashes(repo_id)
        for item in items:
            row = dict(item)
            path = row.get("path") or row.get("file")
            if path:
                row["path"] = path
                if not row.get("content_hash") and path in hashes:
                    row["content_hash"] = hashes[path]
            if not row.get("watched_hashes"):
                watched: dict[str, str] = {}
                ref = str(
                    row.get("source_ref") or row.get("step_id") or row.get("symbol") or ""
                )
                if ref:
                    for hit in self.search(ref.split(".")[-1], limit=20):
                        p = str(hit.get("file_path") or hit.get("path") or "")
                        if p and p in hashes:
                            watched[p] = hashes[p]
                if path and path in hashes:
                    watched[str(path)] = hashes[str(path)]
                if watched:
                    row["watched_hashes"] = watched
            self.conn.execute(
                "INSERT INTO evidence_items("
                "repo_id, run_id, source_type, source_ref, path, status, payload_json, captured_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    repo_id,
                    run_id,
                    str(row.get("type") or "unknown"),
                    str(
                        row.get("source_ref")
                        or row.get("step_id")
                        or row.get("symbol")
                        or ""
                    ),
                    row.get("path"),
                    str(row.get("status") or "observed"),
                    json.dumps(row, ensure_ascii=False),
                    captured,
                ),
            )
        self.conn.commit()
        return len(items)

    def mark_evidence_status(self, ids: list[int], status: str) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        cur = self.conn.execute(
            f"UPDATE evidence_items SET status = ? WHERE id IN ({placeholders})",
            [status, *ids],
        )
        self.conn.commit()
        return int(cur.rowcount)

    def insert_test_results(
        self,
        repo_id: int,
        results: list[dict[str, Any]],
        *,
        run_id: int | None = None,
    ) -> int:
        captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for item in results:
            self.conn.execute(
                "INSERT INTO test_results("
                "repo_id, run_id, step_id, status, exit_code, stdout_tail, stderr_tail, captured_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    repo_id,
                    run_id,
                    item.get("step_id"),
                    str(item.get("status") or "unknown"),
                    item.get("exit_code"),
                    item.get("stdout_tail"),
                    item.get("stderr_tail"),
                    captured,
                ),
            )
        self.conn.commit()
        return len(results)

    def list_test_results(
        self,
        *,
        repo_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        rows = self.conn.execute(
            "SELECT id, run_id, step_id, status, exit_code, captured_at "
            "FROM test_results WHERE repo_id = ? ORDER BY id DESC LIMIT ?",
            (repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_verification_runs(
        self,
        *,
        repo_id: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        rows = self.conn.execute(
            "SELECT id, plan_id, target, revision, state, captured_at "
            "FROM verification_runs WHERE repo_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_evidence(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        repo_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        if repo_id is None:
            repo_id = self._latest_repo_id()
            if repo_id is None:
                return []
        clauses = ["repo_id = ?"]
        params: list[object] = [repo_id]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if query:
            clauses.append("(source_ref LIKE ? OR path LIKE ? OR payload_json LIKE ?)")
            q = f"%{query}%"
            params.extend([q, q, q])
        params.append(limit)
        sql = (
            "SELECT id, source_type, source_ref, path, status, payload_json, captured_at, run_id "
            f"FROM evidence_items WHERE {' AND '.join(clauses)} "
            "ORDER BY id DESC LIMIT ?"
        )
        out: list[dict] = []
        for row in self.conn.execute(sql, params).fetchall():
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                payload = {}
            out.append(
                {
                    "id": row["id"],
                    "type": row["source_type"],
                    "source_ref": row["source_ref"],
                    "path": row["path"],
                    "status": row["status"],
                    "captured_at": row["captured_at"],
                    "run_id": row["run_id"],
                    "payload": payload,
                }
            )
        return out

    def search(self, query: str, limit: int = 50) -> list[dict]:
        # Prefer FTS5, then merge LIKE so qualified names (Class.method) still match leaf queries.
        fts_query = query.strip().replace('"', "")
        if any(ch in fts_query for ch in ".-_/"):
            fts_query = f'"{fts_query}"'
        out: list[dict] = []
        seen: set[tuple] = set()
        try:
            fts_rows = self.conn.execute(
                "SELECT name, path FROM symbols_fts WHERE symbols_fts MATCH ? LIMIT ?",
                (fts_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            fts_rows = []
        for fr in fts_rows:
            rows = self.conn.execute(
                "SELECT s.name, s.kind, s.start_line, s.end_line, f.path AS file_path "
                "FROM symbols s JOIN files f ON f.id = s.file_id "
                "WHERE s.name = ? AND f.path = ?",
                (fr["name"], fr["path"]),
            ).fetchall()
            for row in rows:
                key = (row["name"], row["file_path"], row["start_line"])
                if key in seen:
                    continue
                seen.add(key)
                out.append(dict(row))
        q = f"%{query}%"
        rows = self.conn.execute(
            "SELECT s.name, s.kind, s.start_line, s.end_line, f.path AS file_path "
            "FROM symbols s JOIN files f ON f.id = s.file_id "
            "WHERE s.name LIKE ? OR f.path LIKE ? "
            "ORDER BY s.name LIMIT ?",
            (q, q, max(limit * 2, 50)),
        ).fetchall()
        for row in rows:
            key = (row["name"], row["file_path"], row["start_line"])
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(row))
        return out[:limit]
