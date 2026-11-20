from __future__ import annotations

from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope, symbol_evidence
from witnis.core.gitinfo import (
    git_blame_range,
    git_commit_summary,
    git_diff_hunks,
    git_head,
    git_name_status,
    git_name_status_range,
    git_show_blob,
    git_toplevel,
    git_worktree_name_status,
)
from witnis.core.parse_js import parse_js_source
from witnis.core.parse_python import parse_python_source
from witnis.core.security import is_sensitive_path, scan_text_for_secrets
from witnis.core.store import Store

_JS_COMPARE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def _open_store(db_path: Path) -> Store:
    if not db_path.exists():
        raise FileNotFoundError(f"no index at {db_path}")
    return Store(db_path)


def _repo_meta(repo: dict[str, Any]) -> dict[str, Any]:
    root = Path(repo["root_path"])
    head = git_head(root) or "workdir"
    indexed = repo.get("indexed_revision")
    return {
        "name": repo["name"],
        "root_path": repo["root_path"],
        "revision": head,
        "indexed_revision": indexed,
        "index_stale": bool(indexed and indexed not in {head, "workdir"} and head != "workdir" and indexed != head),
    }


def _stale_bits(repository: dict[str, Any] | None) -> tuple[list[str], list[dict[str, Any]]]:
    if not repository or not repository.get("index_stale"):
        return [], []
    return (
        [
            "STALE: indexed_revision differs from live git HEAD — re-run witnis index",
            f"indexed_revision={repository.get('indexed_revision')!r} live={repository.get('revision')!r}",
        ],
        [
            {
                "type": "index_revision",
                "status": "stale",
                "indexed_revision": repository.get("indexed_revision"),
                "live_revision": repository.get("revision"),
            }
        ],
    )


def repo_overview(db_path: Path) -> dict[str, Any]:
    store = _open_store(db_path)
    try:
        data = store.overview()
        relations = store.list_relations(limit=20)
    finally:
        store.close()
    repo = data.get("repository")
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    repository = _repo_meta(repo)
    stale_limits, stale_evidence = _stale_bits(repository)
    return make_envelope(
        status="success",
        repository=repository,
        result={
            "files": data["files"],
            "symbols": data["symbols"],
            "indexed_revision": repository.get("indexed_revision"),
            "relation_sample": relations,
            "relation_sample_count": len(relations),
        },
        evidence=[
            {
                "type": "index_stats",
                "status": "observed",
                "files": data["files"],
                "symbols": data["symbols"],
            }
        ]
        + stale_evidence
        + [
            {
                "type": "relation",
                "status": edge["status"],
                "source": edge["source"],
                "target": edge["target"],
                "relation_type": edge["relation_type"],
                "lines": [edge.get("start_line"), edge.get("start_line")],
            }
            for edge in relations[:5]
        ],
        limitations=[
            "Python symbols/imports only in current foundation",
            "relation_sample is capped; full graph query comes later",
            "Index may lag the worktree if files changed after last index",
        ]
        + stale_limits,
    )


def repo_search(db_path: Path, query: str, limit: int = 50) -> dict[str, Any]:
    from witnis.core.native import rust_search

    store = _open_store(db_path)
    try:
        overview = store.overview()
        hits = store.search(query, limit=limit)
        backend = "python"
        # Prefer Rust FTS path when native is present and returns hits.
        rust_hits = rust_search(db_path, query, limit=limit)
        if rust_hits:
            hits = rust_hits
            backend = "rust"
    finally:
        store.close()
    repo = overview.get("repository")
    repository = _repo_meta(repo) if repo is not None else None
    if not hits:
        return make_envelope(
            status="partial",
            repository=repository,
            result={"matches": [], "backend": backend},
            limitations=[f"No symbol/path matches for query={query!r}"],
        )
    evidence = [symbol_evidence(h) for h in hits]
    return make_envelope(
        status="success",
        repository=repository,
        result={"matches": hits, "backend": backend},
        evidence=evidence,
        limitations=["Search is name/path FTS+LIKE match, not semantic embedding"],
    )

def trace_symbol(db_path: Path, name: str, limit: int = 50) -> dict[str, Any]:
    """Locate symbol definitions plus call/ref/inherit/override/decorator edges."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        hits = store.search(name, limit=limit)
        short = name.split(".")[-1]

        def _rel(relation_type: str, *, target: bool = False, source: bool = False) -> list:
            rows: list[dict] = []
            if target:
                rows.extend(
                    store.find_relations(
                        relation_type=relation_type, target_equals=short, limit=limit
                    )
                )
                if name != short:
                    rows.extend(
                        store.find_relations(
                            relation_type=relation_type, target_equals=name, limit=limit
                        )
                    )
            if source:
                rows.extend(
                    store.find_relations(
                        relation_type=relation_type,
                        source_contains=f":{short}",
                        limit=limit,
                    )
                )
                if name != short:
                    rows.extend(
                        store.find_relations(
                            relation_type=relation_type,
                            source_contains=f":{name}",
                            limit=limit,
                        )
                    )
            return rows

        outgoing = _rel("calls", source=True)
        incoming = _rel("calls", target=True)
        refs = _rel("references", target=True)
        inherits = _rel("inherits", source=True) + _rel("inherits", target=True)
        overrides = _rel("overrides", source=True) + _rel("overrides", target=True)
        decorated = _rel("decorated_by", source=True) + _rel(
            "decorated_by", target=True
        )
    finally:
        store.close()
    repo = overview.get("repository")
    repository = _repo_meta(repo) if repo is not None else None
    exact = [h for h in hits if h["name"] == name or h["name"].endswith("." + name)]
    chosen = exact or hits

    def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple] = set()
        out: list[dict[str, Any]] = []
        for row in rows:
            key = (
                row.get("source"),
                row.get("target"),
                row.get("relation_type"),
                row.get("start_line"),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
        return out

    outgoing = _dedupe(outgoing)[:limit]
    incoming = _dedupe(incoming)[:limit]
    refs = _dedupe(refs)[:limit]
    inherits = _dedupe(inherits)[:limit]
    overrides = _dedupe(overrides)[:limit]
    decorated = _dedupe(decorated)[:limit]

    if not chosen and not any(
        (outgoing, incoming, refs, inherits, overrides, decorated)
    ):
        return make_envelope(
            status="partial",
            repository=repository,
            result={
                "definitions": [],
                "references": [],
                "calls": [],
                "called_by": [],
                "inherits": [],
                "overrides": [],
                "decorated_by": [],
            },
            limitations=[f"Symbol not found: {name}"],
        )

    evidence = [symbol_evidence(h) for h in chosen]
    for edge in [
        *outgoing,
        *incoming,
        *refs,
        *inherits,
        *overrides,
        *decorated,
    ][:40]:
        evidence.append(
            {
                "type": "relation",
                "status": edge.get("status", "derived"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "relation_type": edge.get("relation_type"),
                "lines": [edge.get("start_line"), edge.get("start_line")],
            }
        )

    status = "success" if exact else "partial"
    limitations = [
        "Call/reference edges are AST based (derived), not fully resolved bindings",
        "Cross-module resolution is incomplete",
    ]
    if not exact:
        limitations.append("Definition match was fuzzy (name search)")

    return make_envelope(
        status=status,
        repository=repository,
        result={
            "definitions": chosen,
            "references": refs,
            "calls": outgoing,
            "called_by": incoming,
            "inherits": inherits,
            "overrides": overrides,
            "decorated_by": decorated,
        },
        evidence=evidence,
        limitations=limitations,
    )


def explain_change(
    db_path: Path, revision: str = "HEAD", limit: int = 50
) -> dict[str, Any]:
    """Explain a git revision using name-status + indexed symbols on touched files."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        root = Path(repo["root_path"])
        meta = git_commit_summary(root, revision)
        if meta is None:
            return make_envelope(
                status="failed",
                repository=_repo_meta(repo),
                result={},
                limitations=[
                    f"Not a git revision or git unavailable: {revision!r}",
                ],
            )
        changes = git_name_status(root, revision)
        store.upsert_commit(int(repo["id"]), meta, files=changes)
        touched_symbols: list[dict[str, Any]] = []
        blob_symbols: list[dict[str, Any]] = []
        blob_misses: list[str] = []
        for change in changes:
            path = change.get("path")
            if not path:
                continue
            path_s = str(path)
            if path_s.endswith(".py") and change.get("status") != "D":
                blob = git_show_blob(root, revision, path_s)
                if blob is None:
                    blob_misses.append(path_s)
                else:
                    for sym in parse_python_source(blob, rel_path=path_s):
                        blob_symbols.append(
                            {
                                "name": sym.name,
                                "kind": sym.kind,
                                "file_path": sym.file_path,
                                "start_line": sym.start_line,
                                "end_line": sym.end_line,
                                "source": "historical_blob",
                                "revision": meta["hash"],
                            }
                        )
            for hit in store.search(path_s, limit=limit):
                if hit.get("file_path") == path_s or path_s.endswith(
                    str(hit.get("file_path"))
                ):
                    touched_symbols.append(hit)
        # Prefer historical blob symbols when present; fall back to index.
        preferred = blob_symbols or touched_symbols
        seen: set[tuple] = set()
        unique_symbols: list[dict[str, Any]] = []
        for hit in preferred:
            key = (hit.get("file_path"), hit.get("name"), hit.get("start_line"))
            if key in seen:
                continue
            seen.add(key)
            unique_symbols.append(hit)
    finally:
        store.close()

    evidence: list[dict[str, Any]] = [
        {
            "type": "commit",
            "status": "observed",
            "hash": meta["hash"],
            "subject": meta["subject"],
            "committed_at": meta["committed_at"],
        }
    ]
    for change in changes[:30]:
        evidence.append(
            {
                "type": "file_change",
                "status": "observed",
                "change_status": change.get("status"),
                "file": change.get("path"),
                "from_file": change.get("from_path"),
            }
        )
    for hit in unique_symbols[:30]:
        if hit.get("source") == "historical_blob":
            evidence.append(
                {
                    "type": "historical_symbol",
                    "status": "observed",
                    "symbol": hit.get("name"),
                    "kind": hit.get("kind"),
                    "file": hit.get("file_path"),
                    "lines": [hit.get("start_line"), hit.get("end_line")],
                    "revision": hit.get("revision"),
                }
            )
        else:
            evidence.append(symbol_evidence(hit))

    hunks = git_diff_hunks(root, revision)
    symbols_in_hunks: list[dict[str, Any]] = []
    for sym in unique_symbols:
        path = str(sym.get("file_path") or "")
        try:
            s_line = int(sym.get("start_line") or 0)
            e_line = int(sym.get("end_line") or s_line)
        except (TypeError, ValueError):
            continue
        for hunk in hunks:
            if hunk.get("path") != path:
                continue
            h_s = int(hunk["start_line"])
            h_e = int(hunk["end_line"])
            if s_line <= h_e and e_line >= h_s:
                symbols_in_hunks.append({**sym, "hunk": hunk})
                break
    for hit in symbols_in_hunks[:20]:
        evidence.append(
            {
                "type": "hunk_symbol",
                "status": "derived",
                "symbol": hit.get("name"),
                "file": hit.get("file_path"),
                "lines": [hit.get("start_line"), hit.get("end_line")],
                "hunk_lines": [
                    (hit.get("hunk") or {}).get("start_line"),
                    (hit.get("hunk") or {}).get("end_line"),
                ],
            }
        )

    limitations = [
        "Commit message is observed text, not verified intent",
    ]
    if blob_symbols:
        limitations.append("Python symbols for touched files are parsed from git blobs at revision")
    else:
        limitations.append(
            "Symbol mapping fell back to the current index (no usable historical blobs)"
        )
    if blob_misses:
        limitations.append(
            f"Could not read historical blobs for: {', '.join(blob_misses[:5])}"
        )
    if hunks:
        limitations.append("symbols_in_hunks overlaps unified-diff new-file ranges (unified=0)")
    else:
        limitations.append("No parseable unified-diff hunks for this revision")
    toplevel = git_toplevel(root)
    if toplevel is not None and toplevel != root.resolve():
        limitations.append(
            f"Indexed path is inside git toplevel {toplevel}; "
            "revision metadata refers to that repository"
        )
    if not changes:
        limitations.append("No file changes listed for this revision")

    return make_envelope(
        status="success" if changes else "partial",
        repository={
            "name": repo["name"],
            "root_path": repo["root_path"],
            "revision": meta["hash"],
        },
        result={
            "commit": meta,
            "files": changes,
            "hunks": hunks[:limit],
            "symbols_in_touched_files": unique_symbols[:limit],
            "symbols_in_hunks": symbols_in_hunks[:limit],
        },
        evidence=evidence,
        limitations=limitations,
    )


def analyze_change_impact(
    db_path: Path, revision: str = "HEAD", limit: int = 50
) -> dict[str, Any]:
    """Blast radius for symbols overlapping diff hunks in a revision."""
    change = explain_change(db_path, revision=revision, limit=limit)
    if change["status"] == "failed":
        return change

    hunk_syms = change.get("result", {}).get("symbols_in_hunks") or []
    if not hunk_syms:
        # Fall back to any touched-file symbols when hunk overlap is empty.
        hunk_syms = change.get("result", {}).get("symbols_in_touched_files") or []

    direct: list[dict[str, Any]] = []
    transitive: list[dict[str, Any]] = []
    related_tests: list[dict[str, Any]] = []
    evidence = list(change.get("evidence") or [])[:20]
    limitations = list(change.get("limitations") or [])

    for sym in hunk_syms[:10]:
        name = str(sym.get("name") or "")
        if not name:
            continue
        impact = analyze_impact(db_path, name, limit=limit)
        direct.extend(impact.get("result", {}).get("direct") or [])
        transitive.extend(impact.get("result", {}).get("transitive") or [])
        related_tests.extend(impact.get("result", {}).get("related_tests") or [])
        evidence.extend(impact.get("evidence") or [])

    direct = _dedupe_edges(direct)[:limit]
    transitive = _dedupe_edges(transitive)[:limit]
    # de-dupe tests by file+name
    seen_t: set[tuple] = set()
    unique_tests: list[dict[str, Any]] = []
    for t in related_tests:
        key = (t.get("file_path"), t.get("name"))
        if key in seen_t:
            continue
        seen_t.add(key)
        unique_tests.append(t)

    limitations.append(
        "Change impact unions per-symbol impact for hunk-overlapping symbols"
    )

    return make_envelope(
        status="success" if hunk_syms else "partial",
        repository=change.get("repository"),
        result={
            "revision": change.get("result", {}).get("commit"),
            "symbols_in_hunks": hunk_syms[:limit],
            "direct": direct,
            "transitive": transitive[:limit],
            "related_tests": unique_tests[:limit],
        },
        evidence=evidence[: limit * 2],
        limitations=limitations,
    )


def _dedupe_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Collapse (1) qualified vs bare target aliases of the same site and
    # (2) a ``calls`` + ``references`` pair emitted for one Python call.
    # Distinct receivers on the same line (Owner.getName vs Pet.getName) stay.
    index: dict[tuple, list[int]] = {}
    out: list[dict[str, Any]] = []
    pairable = {"calls", "references"}
    for row in rows:
        target = str(row.get("target") or "")
        leaf = target.rsplit(".", 1)[-1]
        rel = str(row.get("relation_type") or "")
        key = (row.get("source"), leaf, row.get("start_line"))
        merged = False
        for pos in index.setdefault(key, []):
            kept = out[pos]
            kept_tgt = str(kept.get("target") or "")
            kept_rel = str(kept.get("relation_type") or "")
            alias = kept_tgt == target or leaf in (kept_tgt, target)
            same_kind = kept_rel == rel or {kept_rel, rel} <= pairable
            if not (alias and same_kind):
                continue
            merged_row = dict(kept)
            if len(target) > len(kept_tgt):
                merged_row["target"] = target
            if "calls" in (kept_rel, rel):
                merged_row["relation_type"] = "calls"
            out[pos] = merged_row
            merged = True
            break
        if not merged:
            index[key].append(len(out))
            out.append(dict(row))
    return out


def analyze_impact(
    db_path: Path, target: str, limit: int = 50
) -> dict[str, Any]:
    """Estimate blast radius for a symbol or file using indexed relations."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        repository = _repo_meta(repo) if repo is not None else None
        short = target.split(".")[-1]
        defs = store.search(target, limit=limit)
        exact_defs = [
            h for h in defs if h["name"] == target or h["name"].endswith("." + target)
        ]

        def _edges(rel: str) -> list[dict[str, Any]]:
            return _dedupe_edges(
                store.find_relations(
                    relation_type=rel,
                    target_equals=short,
                    target_suffix=short,
                    limit=limit,
                )
                + (
                    store.find_relations(
                        relation_type=rel,
                        target_equals=target,
                        target_suffix=short,
                        limit=limit,
                    )
                    if target != short
                    else []
                )
            )

        direct_calls = _dedupe_edges(_edges("calls") + _edges("references"))
        # Drop tautological self edges (method body matching its own name).
        direct_calls = [
            e
            for e in direct_calls
            if not (
                str(e.get("relation_type")) == "calls"
                and str(e.get("source") or "").endswith("." + short)
                and str(e.get("target") or "") in {short, target}
            )
        ]
        subclasses = _dedupe_edges(
            _edges("inherits")
        )
        injections = _edges("injects")
        implementations = _edges("implements")
        type_users = _edges("uses_type")
        decorated = _dedupe_edges(
            store.find_relations(
                relation_type="decorated_by", target_equals=short, limit=limit
            )
            + store.find_relations(
                relation_type="decorated_by", source_contains=short, limit=limit
            )
        )
        overrides = _dedupe_edges(
            store.find_relations(
                relation_type="overrides", target_equals=short, limit=limit
            )
            + store.find_relations(
                relation_type="overrides", target_equals=target, limit=limit
            )
            + store.find_relations(
                relation_type="overrides", source_contains=short, limit=limit
            )
        )
        importers = _dedupe_edges(
            store.find_relations(
                relation_type="imports_from", target_equals=target, limit=limit
            )
            + store.find_relations(
                relation_type="imports_from",
                target_equals=short,
                limit=limit,
            )
            + store.find_relations(
                relation_type="imports", target_equals=short, limit=limit
            )
        )
        # Also match imports like auth.AuthService
        for edge in store.list_relations(limit=500):
            if edge["relation_type"] not in {"imports", "imports_from"}:
                continue
            tgt = str(edge.get("target") or "")
            if tgt == target or tgt.endswith("." + short) or short in tgt.split("."):
                importers.append(edge)
        importers = _dedupe_edges(importers)[:limit]

        # one-hop transitive: callers of direct callers (F4 — short-name Uncertain)
        call_follow: list[dict[str, Any]] = []
        for edge in direct_calls[:20]:
            caller = str(edge.get("source") or "")
            caller_name = caller.split(":")[-1] if ":" in caller else caller
            leaf = caller_name.split(".")[-1]
            # Skip tiny/common leaves that collide across the index (F4 harden).
            if len(leaf) < 4 or leaf.lower() in {
                "get", "set", "call", "run", "main", "init", "test", "data"
            }:
                continue
            call_follow.extend(
                store.find_relations(
                    relation_type="calls", target_equals=leaf, limit=20
                )
            )
        # Typed users of subclasses (Owner←Person → controllers uses_type Owner)
        typed_follow: list[dict[str, Any]] = []
        subclass_leaves: set[str] = set()
        for edge in subclasses:
            src = str(edge.get("source") or "")
            leaf = src.split(":")[-1].split(".")[-1] if src else ""
            if leaf and leaf != short:
                subclass_leaves.add(leaf)
        for leaf in subclass_leaves:
            typed_follow.extend(
                store.find_relations(
                    relation_type="uses_type", target_equals=leaf, limit=limit
                )
            )
        # Production impact only: drop test-source typed users (SCOPE / Test link).
        def _is_test_source(edge: dict[str, Any]) -> bool:
            src = str(edge.get("source") or "").replace("\\", "/").lower()
            return "/test/" in src or src.startswith("test/")

        typed_follow = [e for e in typed_follow if not _is_test_source(e)]
        direct_keys = {(d.get("source"), d.get("target")) for d in (
            direct_calls + importers + subclasses + decorated + overrides
            + injections + implementations + type_users
        )}
        uncertain_calls = [
            {**e, "status": "uncertain"}
            for e in _dedupe_edges(call_follow)
            if (e.get("source"), e.get("target")) not in direct_keys
        ]
        typed_indirect = [
            e
            for e in _dedupe_edges(typed_follow)
            if (e.get("source"), e.get("target")) not in direct_keys
        ]
        transitive = (typed_indirect + uncertain_calls)[:limit]
    finally:
        store.close()

    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )

    related_tests = find_related_tests(db_path, target, limit=limit)["result"].get(
        "tests", []
    )

    direct_pack = (
        direct_calls
        + importers
        + subclasses
        + decorated
        + overrides
        + injections
        + implementations
        + type_users
    )
    impact = {
        "direct": [
            {**e, "impact_level": "Direct"}
            for e in direct_pack[:limit]
        ],
        "transitive": [{**e, "impact_level": "Transitive"} for e in transitive],
        "related_tests": related_tests,
        "definitions": exact_defs or defs[:5],
    }
    stale_limits, stale_evidence = _stale_bits(repository)
    evidence: list[dict[str, Any]] = [symbol_evidence(h) for h in (exact_defs or defs)[:10]]
    evidence.extend(stale_evidence)
    for edge in (direct_pack + transitive)[:30]:
        evidence.append(
            {
                "type": "relation",
                "status": edge.get("status", "derived"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "relation_type": edge.get("relation_type"),
                "impact_level": edge.get("impact_level"),
                "lines": [edge.get("start_line"), edge.get("start_line")],
            }
        )

    has_signal = bool(
        direct_pack
        or transitive
        or exact_defs
        or defs
    )
    return make_envelope(
        status="success" if has_signal else "partial",
        repository=repository,
        result=impact,
        evidence=evidence,
        limitations=[
            "Impact is relation-index based, not runtime-proven",
            "Transitive edges are one-hop and may include name collisions (Uncertain)",
            "Import matching is stringly typed across modules",
            "DI/implements edges are framework-pattern derived (not container-proven)",
            "uses_type is signature-derived (params/returns); not full flow-sensitive typing",
        ]
        + stale_limits,
    )


def check_import_graph(db_path: Path, limit: int = 100) -> dict[str, Any]:
    """Check indexed import edges against known files/modules in the index."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        repository = _repo_meta(repo) if repo is not None else None
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        files = {
            str(r["path"]).replace("\\", "/")
            for r in store.conn.execute(
                "SELECT path FROM files WHERE repo_id = ?", (repo["id"],)
            ).fetchall()
        }
        modules = set()
        for path in files:
            if not path.endswith(".py"):
                continue
            mod = path[:-3].replace("/", ".")
            if mod.endswith(".__init__"):
                mod = mod[: -len(".__init__")]
            modules.add(mod)
            modules.add(mod.split(".")[-1])
            # package roots
            parts = mod.split(".")
            for i in range(1, len(parts)):
                modules.add(".".join(parts[:i]))

        broken: list[dict[str, Any]] = []
        ok_count = 0
        skipped_external = 0
        for edge in store.list_relations(limit=1000):
            if edge.get("relation_type") not in {"imports", "imports_from"}:
                continue
            tgt = str(edge.get("target") or "").strip()
            if not tgt:
                continue
            root_mod = tgt.split(".")[0]
            # External/stdlib/third-party: root not present in indexed modules.
            if root_mod not in modules:
                skipped_external += 1
                continue
            as_file = tgt.replace(".", "/") + ".py"
            as_pkg = tgt.replace(".", "/") + "/__init__.py"
            # Attribute imports (auth.AuthService) resolve via root module.
            resolved = (
                tgt in modules
                or root_mod in modules
                or as_file in files
                or as_pkg in files
                or any(f.endswith("/" + Path(as_file).name) for f in files if as_file.count("/") == 0)
            )
            # For dotted module paths, require file/package match or symbol-bearing module.
            if "." in tgt and root_mod in modules:
                # auth.AuthService is fine if auth.py exists; auth.missing_mod.foo is not
                # if second segment looks like a submodule path that isn't a known module.
                parts = tgt.split(".")
                if len(parts) >= 2:
                    maybe_sub = ".".join(parts[:2])
                    sub_file = maybe_sub.replace(".", "/") + ".py"
                    sub_pkg = maybe_sub.replace(".", "/") + "/__init__.py"
                    if (
                        maybe_sub in modules
                        or sub_file in files
                        or sub_pkg in files
                        or root_mod in modules
                    ):
                        # Treat attribute import off a known module as resolved.
                        resolved = True
            if resolved:
                ok_count += 1
            else:
                broken.append(
                    {
                        "source": edge.get("source"),
                        "target": tgt,
                        "relation_type": edge.get("relation_type"),
                        "status": "uncertain",
                    }
                )
                if len(broken) >= limit:
                    break
    finally:
        store.close()

    evidence = [
        {
            "type": "import_graph",
            "status": "verified" if not broken else "uncertain",
            "ok_count": ok_count,
            "broken_count": len(broken),
            "skipped_external": skipped_external,
        }
    ]
    for row in broken[:20]:
        evidence.append(
            {
                "type": "broken_import",
                "status": "uncertain",
                "source": row.get("source"),
                "target": row.get("target"),
            }
        )

    return make_envelope(
        status="success" if not broken else "partial",
        repository=repository,
        result={
            "ok": ok_count,
            "broken": broken,
            "broken_count": len(broken),
            "skipped_external": skipped_external,
        },
        evidence=evidence,
        limitations=[
            "External imports (root module not in index) are skipped, not failed",
            "Only imports/imports_from edges are checked",
        ],
    )


_TEST_DIRS = {"tests", "test", "__tests__", "spec"}
_TEST_SUFFIXES = (
    "_test.py", "_test.go", "Test.java", "Tests.java", "IT.java",
    ".test.js", ".test.ts", ".test.jsx", ".test.tsx",
    ".spec.js", ".spec.ts", ".spec.jsx", ".spec.tsx",
)


def is_test_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    base = parts[-1]
    if base.startswith("test_") and base.endswith(".py"):
        return True
    if base.endswith(_TEST_SUFFIXES):
        return True
    return any(p in _TEST_DIRS for p in parts[:-1])


def look_symbol(db_path: Path, target: str) -> dict[str, Any]:
    """Compact witness card used by `witnis look` and the public MCP `look` tool."""
    from witnis.core.verify import create_verification_plan

    search = repo_search(db_path, query=target, limit=8)
    trace = trace_symbol(db_path, name=target)
    impact = analyze_impact(db_path, target=target)
    tests = find_related_tests(db_path, target=target)
    plan = create_verification_plan(db_path, target=target)
    matches = (search.get("result") or {}).get("matches") or []
    defs = (trace.get("result") or {}).get("definitions") or []
    called_by = (trace.get("result") or {}).get("called_by") or []
    direct = (impact.get("result") or {}).get("direct") or []
    related = (tests.get("result") or {}).get("tests") or []
    steps = (plan.get("result") or {}).get("steps") or []
    lines = [target]
    if matches:
        m = matches[0]
        lines.append(
            f"  hit     {m.get('kind')}  {m.get('name')}  "
            f"{m.get('file_path')}:{m.get('start_line')}"
        )
    for d in defs[:3]:
        lines.append(
            f"  def     {d.get('kind')}  {d.get('name')}  "
            f"{d.get('file_path')}:{d.get('start_line')}"
        )
    caller_lines: dict[str, list[str]] = {}
    for edge in called_by:
        rows = caller_lines.setdefault(str(edge.get("source")), [])
        line = edge.get("start_line")
        if line is not None and f":{line}" not in rows:
            rows.append(f":{line}")
    for source, rows in list(caller_lines.items())[:4]:
        lines.append(f"  caller  {source}  {' '.join(rows)}".rstrip())
    lines.append(f"  impact  {len(direct)} direct edge(s)")
    if related:
        paths = ", ".join(sorted({str(t.get("file_path")) for t in related[:5]}))
        lines.append(f"  tests   {paths}")
    else:
        lines.append("  tests   (none indexed)")
    lines.append(
        f"  plan    {len(steps)} step(s) — run: witnis verify {target} --execute"
    )
    return make_envelope(
        status="success" if defs or matches else "partial",
        repository=impact.get("repository") or search.get("repository"),
        result={
            "card": "\n".join(lines),
            "direct_count": len(direct),
            "definitions": defs[:5],
            "tests": related[:10],
            "plan_steps": len(steps),
        },
        evidence=list(impact.get("evidence") or [])[:8],
        limitations=list(impact.get("limitations") or [])[:6],
    )


def find_related_tests(
    db_path: Path, target: str, limit: int = 50
) -> dict[str, Any]:
    """Find likely related tests by path/name heuristics + import/call edges."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        repository = _repo_meta(repo) if repo is not None else None
        short = target.split(".")[-1]
        tests: list[dict[str, Any]] = []

        # symbols in test-looking files that mention target
        for hit in store.search(short, limit=200):
            path = str(hit.get("file_path") or "")
            if not is_test_path(path):
                continue
            tests.append({**hit, "reason": "symbol_in_test_path"})

        edges = store.find_relations(target_suffix=short, limit=2000)
        edges += store.find_relations(source_contains=short, limit=2000)
        for edge in edges:
            src = str(edge.get("source") or "")
            path = src.split(":")[0]
            if not is_test_path(path):
                continue
            tgt = str(edge.get("target") or "")
            if short in tgt or target in tgt or short in src:
                tests.append(
                    {
                        "file_path": path,
                        "name": src,
                        "kind": "relation",
                        "relation": edge,
                        "reason": "test_relation_to_target",
                    }
                )
    finally:
        store.close()

    # dedupe
    seen: set[tuple] = set()
    unique: list[dict[str, Any]] = []
    for row in tests:
        key = (row.get("file_path"), row.get("name"), row.get("reason"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    return make_envelope(
        status="success" if unique else "partial",
        repository=repository,
        result={"tests": unique[:limit], "target": target},
        evidence=[
            {
                "type": "test_heuristic",
                "status": "derived",
                "file": t.get("file_path"),
                "symbol": t.get("name"),
                "reason": t.get("reason"),
            }
            for t in unique[:20]
        ],
        limitations=[
            "Test discovery is heuristic (path names + relations), not runner integration",
        ],
    )


def get_evidence(
    db_path: Path,
    query: str,
    limit: int = 50,
    *,
    status: str | None = None,
) -> dict[str, Any]:
    """Collect observed/derived/persisted evidence for a symbol or path query."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        repository = _repo_meta(repo) if repo is not None else None
        short = query.split(".")[-1]
        symbols = store.search(query, limit=limit) if not status else []
        relations = (
            _dedupe_edges(
                store.find_relations(target_equals=short, limit=limit)
                + store.find_relations(source_contains=short, limit=limit)
                + store.find_relations(target_equals=query, limit=limit)
            )[:limit]
            if not status
            else []
        )
        stored = store.find_evidence(query=query or None, status=status, limit=limit)
    finally:
        store.close()

    evidence: list[dict[str, Any]] = []
    if not status:
        evidence.extend(symbol_evidence(h) for h in symbols)
        for edge in relations:
            evidence.append(
                {
                    "type": "relation",
                    "status": edge.get("status", "derived"),
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "relation_type": edge.get("relation_type"),
                    "lines": [edge.get("start_line"), edge.get("start_line")],
                }
            )
    for row in stored:
        evidence.append(
            {
                "type": row.get("type"),
                "status": row.get("status"),
                "source_ref": row.get("source_ref"),
                "path": row.get("path"),
                "captured_at": row.get("captured_at"),
                "run_id": row.get("run_id"),
                "payload": row.get("payload"),
            }
        )

    return make_envelope(
        status="success" if evidence else "partial",
        repository=repository,
        result={
            "query": query,
            "status_filter": status,
            "symbols": symbols,
            "relations": relations,
            "stored_count": len(stored),
        },
        evidence=evidence[: limit * 2],
        limitations=[
            "Live index evidence mixes with persisted verification evidence",
            "Historical blob symbols are available via explain_change, not this query",
        ],
    )


def explain_code(
    db_path: Path,
    name: str,
    limit: int = 20,
    *,
    revision: str | None = None,
) -> dict[str, Any]:
    """Explain a symbol with definition location, snippet, callers, and blame."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        hits = store.search(name, limit=limit)
    finally:
        store.close()
    repository = _repo_meta(repo) if repo else None
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    exact = [h for h in hits if h["name"] == name or h["name"].endswith("." + name)]
    chosen = (exact or hits)[:1]
    if not chosen:
        return make_envelope(
            status="partial",
            repository=repository,
            result={"definitions": []},
            limitations=[f"Symbol not found: {name}"],
        )
    symbol = dict(chosen[0])
    root = Path(repo["root_path"])
    snippet = []
    snippet_source = "workdir"
    file_path = root / symbol["file_path"]
    blob_text: str | None = None
    if revision:
        blob_text = git_show_blob(root, revision, str(symbol["file_path"]))
        if blob_text is not None and str(symbol["file_path"]).endswith(".py"):
            blob_syms = parse_python_source(
                blob_text, rel_path=str(symbol["file_path"])
            )
            match = next(
                (
                    s
                    for s in blob_syms
                    if s.name == symbol["name"]
                    or s.name.endswith("." + name)
                    or symbol["name"].endswith("." + s.name)
                ),
                None,
            )
            if match:
                symbol["start_line"] = match.start_line
                symbol["end_line"] = match.end_line
                symbol["kind"] = match.kind
            lines = blob_text.splitlines()
            start = max(1, int(symbol["start_line"]))
            end = min(len(lines), int(symbol["end_line"]))
            for i in range(start, end + 1):
                snippet.append({"line": i, "text": lines[i - 1]})
            snippet_source = "historical_blob"
            evidence_blob = {
                "type": "historical_snippet",
                "status": "observed",
                "file": symbol["file_path"],
                "revision": revision,
                "lines": [start, end],
            }
        elif blob_text is not None:
            lines = blob_text.splitlines()
            start = max(1, int(symbol["start_line"]))
            end = min(len(lines), int(symbol["end_line"]))
            for i in range(start, end + 1):
                if i <= len(lines):
                    snippet.append({"line": i, "text": lines[i - 1]})
            snippet_source = "historical_blob"
            evidence_blob = {
                "type": "historical_snippet",
                "status": "observed",
                "file": symbol["file_path"],
                "revision": revision,
                "lines": [start, end],
            }
        else:
            evidence_blob = None
    else:
        evidence_blob = None
        if file_path.is_file():
            lines = file_path.read_text(encoding="utf-8").splitlines()
            start = max(1, int(symbol["start_line"]))
            end = min(len(lines), int(symbol["end_line"]))
            for i in range(start, end + 1):
                snippet.append({"line": i, "text": lines[i - 1]})
    try:
        blame = git_blame_range(
            root,
            symbol["file_path"],
            int(symbol["start_line"]),
            int(symbol["end_line"]),
        )
    except Exception:
        blame = []
    traced = trace_symbol(db_path, symbol["name"], limit=limit)
    evidence = [symbol_evidence(symbol)]
    if evidence_blob:
        evidence.append(evidence_blob)
    for row in blame[:10]:
        evidence.append(
            {
                "type": "blame",
                "status": "observed" if row.get("commit") else "unverified",
                "file": symbol["file_path"],
                "line": row.get("line"),
                "commit": row.get("commit"),
                "author": row.get("author"),
                "summary": row.get("summary"),
            }
        )
    evidence.extend(traced.get("evidence") or [])

    limitations = [
        "Blame may refer to the enclosing git toplevel if fixture is nested",
    ]
    if snippet_source == "historical_blob":
        limitations.append(f"Snippet parsed from git blob at {revision}")
    else:
        limitations.append("Snippet is from the working tree, not a historical blob")
    limitations.extend(traced.get("limitations") or [])

    return make_envelope(
        status="success",
        repository=repository,
        result={
            "symbol": symbol,
            "snippet": snippet,
            "snippet_source": snippet_source,
            "revision": revision,
            "blame": blame,
            "calls": traced.get("result", {}).get("calls") or [],
            "called_by": traced.get("result", {}).get("called_by") or [],
        },
        evidence=evidence,
        limitations=limitations,
    )

def check_python_syntax(
    db_path: Path, paths: list[str] | None = None, limit: int = 200
) -> dict[str, Any]:
    """AST-parse Python files under the indexed repo (in-process syntax check)."""
    import ast

    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        root = Path(repo["root_path"])
        if paths:
            candidates = [p for p in paths if str(p).endswith(".py")]
        else:
            rows = store.conn.execute(
                "SELECT path FROM files WHERE repo_id = ? ORDER BY path LIMIT ?",
                (repo["id"], limit),
            ).fetchall()
            candidates = [str(r["path"]) for r in rows if str(r["path"]).endswith(".py")]
    finally:
        store.close()

    errors: list[dict[str, Any]] = []
    checked = 0
    for rel in candidates[:limit]:
        path = root / rel
        if not path.is_file():
            continue
        checked += 1
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            errors.append(
                {
                    "path": rel,
                    "lineno": exc.lineno,
                    "msg": exc.msg,
                    "text": (exc.text or "").strip(),
                }
            )
        except UnicodeDecodeError as exc:
            errors.append({"path": rel, "msg": f"decode error: {exc}"})

    return make_envelope(
        status="success" if not errors else "partial",
        repository=_repo_meta(repo),
        result={"checked": checked, "errors": errors, "error_count": len(errors)},
        evidence=[
            {
                "type": "syntax_check",
                "status": "verified" if not errors else "failed",
                "checked": checked,
                "error_count": len(errors),
            }
        ],
        limitations=["Only AST parse; does not import modules or run code"],
    )


def _symbols_from_blob(path: str, blob: str | None) -> dict[str, Any]:
    if blob is None:
        return {}
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        syms = parse_python_source(blob, rel_path=path)
    elif suffix in _JS_COMPARE_SUFFIXES:
        syms = parse_js_source(blob, rel_path=path)
    else:
        return {}
    return {s.name: s for s in syms}


def compare_revisions(
    db_path: Path,
    *,
    base: str,
    head: str = "HEAD",
    limit: int = 100,
) -> dict[str, Any]:
    """Compare Python/JS/TS symbol sets between two git revisions for changed files."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    root = Path(repo["root_path"])
    base_meta = git_commit_summary(root, base)
    head_meta = git_commit_summary(root, head)
    if base_meta is None or head_meta is None:
        return make_envelope(
            status="failed",
            repository=_repo_meta(repo),
            result={},
            limitations=[f"Unable to resolve revisions: {base!r} .. {head!r}"],
        )
    changes = git_name_status_range(root, base_meta["hash"], head_meta["hash"])
    symbols_added: list[dict[str, Any]] = []
    symbols_removed: list[dict[str, Any]] = []
    files_touched: list[dict[str, Any]] = []

    for change in changes[:limit]:
        path = str(change.get("path") or "")
        files_touched.append(change)
        suffix = Path(path).suffix.lower()
        if suffix != ".py" and suffix not in _JS_COMPARE_SUFFIXES:
            continue
        old_blob = (
            None
            if change.get("status") == "A"
            else git_show_blob(root, base_meta["hash"], path)
        )
        if change.get("status") == "R" and change.get("from_path"):
            old_blob = git_show_blob(
                root, base_meta["hash"], str(change.get("from_path"))
            )
        new_blob = (
            None
            if change.get("status") == "D"
            else git_show_blob(root, head_meta["hash"], path)
        )
        old_names = _symbols_from_blob(path, old_blob)
        new_names = _symbols_from_blob(path, new_blob)
        for name, sym in new_names.items():
            if name not in old_names:
                symbols_added.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file_path": path,
                        "start_line": sym.start_line,
                    }
                )
        for name, sym in old_names.items():
            if name not in new_names:
                symbols_removed.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file_path": path,
                        "start_line": sym.start_line,
                    }
                )

    evidence = [
        {
            "type": "revision_compare",
            "status": "observed",
            "base": base_meta["hash"],
            "head": head_meta["hash"],
            "files": len(files_touched),
            "added": len(symbols_added),
            "removed": len(symbols_removed),
        }
    ]
    return make_envelope(
        status="success" if changes else "partial",
        repository={
            **_repo_meta(repo),
            "base": base_meta["hash"],
            "head": head_meta["hash"],
        },
        result={
            "base": base_meta,
            "head": head_meta,
            "files": files_touched[:limit],
            "symbols_added": symbols_added[:limit],
            "symbols_removed": symbols_removed[:limit],
        },
        evidence=evidence,
        limitations=[
            "Symbol delta covers Python AST + shallow JS/TS regex symbols on changed paths",
            "Renames use the new path for added symbols and from_path for removed",
        ],
    )


def compare_worktree(db_path: Path, limit: int = 100) -> dict[str, Any]:
    """Compare worktree (including untracked) against HEAD for symbol deltas."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    root = Path(repo["root_path"])
    head_meta = git_commit_summary(root, "HEAD")
    if head_meta is None:
        return make_envelope(
            status="failed",
            repository=_repo_meta(repo),
            result={},
            limitations=["Not a git repository or HEAD unavailable"],
        )
    changes = git_worktree_name_status(root)
    symbols_added: list[dict[str, Any]] = []
    symbols_removed: list[dict[str, Any]] = []
    files_touched: list[dict[str, Any]] = []
    for change in changes[:limit]:
        path = str(change.get("path") or "")
        files_touched.append(change)
        suffix = Path(path).suffix.lower()
        if suffix != ".py" and suffix not in _JS_COMPARE_SUFFIXES:
            continue
        old_blob = git_show_blob(root, head_meta["hash"], path)
        if change.get("status") == "R" and change.get("from_path"):
            old_blob = git_show_blob(root, head_meta["hash"], str(change["from_path"]))
        work_path = root / path
        new_blob = None
        if change.get("status") != "D" and work_path.is_file():
            try:
                new_blob = work_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                new_blob = None
        old_names = _symbols_from_blob(path, old_blob)
        new_names = _symbols_from_blob(path, new_blob)
        for name, sym in new_names.items():
            if name not in old_names:
                symbols_added.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file_path": path,
                        "start_line": sym.start_line,
                    }
                )
        for name, sym in old_names.items():
            if name not in new_names:
                symbols_removed.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file_path": path,
                        "start_line": sym.start_line,
                    }
                )
    return make_envelope(
        status="success" if changes else "partial",
        repository={**_repo_meta(repo), "head": head_meta["hash"]},
        result={
            "head": head_meta,
            "files": files_touched[:limit],
            "symbols_added": symbols_added[:limit],
            "symbols_removed": symbols_removed[:limit],
        },
        evidence=[
            {
                "type": "worktree_compare",
                "status": "observed",
                "files": len(files_touched),
                "added": len(symbols_added),
                "removed": len(symbols_removed),
            }
        ],
        limitations=[
            "Compares worktree+index+untracked against HEAD blobs",
            "Only Python/JS/TS symbol extraction on changed paths",
        ],
    )


def check_index_health(db_path: Path) -> dict[str, Any]:
    """Self-check index integrity: counts, FTS coverage, empty relation targets."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        repo_id = int(repo["id"])
        files = store.file_count(repo_id)
        symbols = store.symbol_count(repo_id)
        rels = store.list_relations(repo_id=repo_id, limit=5000)
        issues: list[dict[str, Any]] = []
        if files == 0:
            issues.append({"code": "no_files", "detail": "Repository has zero indexed files"})
        if symbols == 0:
            issues.append({"code": "no_symbols", "detail": "Repository has zero symbols"})
        try:
            fts = store.conn.execute("SELECT COUNT(*) AS c FROM symbols_fts").fetchone()["c"]
        except Exception as exc:  # noqa: BLE001
            fts = -1
            issues.append({"code": "fts_missing", "detail": str(exc)})
        if fts >= 0 and fts < symbols:
            issues.append(
                {
                    "code": "fts_underfilled",
                    "detail": f"FTS rows={fts} < symbols={symbols}",
                }
            )
        empty_targets = [
            e for e in rels if not str(e.get("target") or "").strip()
        ]
        if empty_targets:
            issues.append(
                {
                    "code": "empty_relation_targets",
                    "detail": f"{len(empty_targets)} relations lack targets",
                }
            )
        # Round-trip: search for a known symbol name if any exist
        sample = store.conn.execute(
            "SELECT name FROM symbols LIMIT 1"
        ).fetchone()
        if sample:
            hits = store.search(str(sample["name"]), limit=5)
            if not hits:
                issues.append(
                    {
                        "code": "search_miss",
                        "detail": f"search({sample['name']!r}) returned no hits",
                    }
                )
    finally:
        store.close()

    return make_envelope(
        status="success" if not issues else "partial",
        repository=_repo_meta(repo),
        result={
            "files": files,
            "symbols": symbols,
            "relations_sampled": len(rels),
            "fts_rows": fts,
            "issues": issues,
        },
        evidence=[
            {
                "type": "index_health",
                "status": "verified" if not issues else "uncertain",
                "issue_count": len(issues),
            }
        ],
        limitations=["Health check is structural, not semantic correctness of edges"],
    )


def export_evidence_bundle(
    db_path: Path,
    *,
    target: str | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Pack overview/trace/impact/tests/(optional change) into one agent-facing bundle."""
    overview = repo_overview(db_path)
    if overview["status"] == "failed":
        return overview

    repository = overview.get("repository")
    evidence: list[dict[str, Any]] = list(overview.get("evidence") or [])[:10]
    limitations = [
        "Bundle is a convenience aggregate; prefer primary tools for live queries",
    ]
    bundle: dict[str, Any] = {
        "target": target,
        "revision": revision,
        "overview": overview.get("result"),
    }

    if target:
        bundle["search"] = repo_search(db_path, target, limit=limit).get("result")
        traced = trace_symbol(db_path, target, limit=limit)
        bundle["trace"] = traced.get("result")
        evidence.extend(traced.get("evidence") or [])
        impact = analyze_impact(db_path, target, limit=limit)
        bundle["impact"] = impact.get("result")
        evidence.extend(impact.get("evidence") or [])
        tests = find_related_tests(db_path, target, limit=limit)
        bundle["related_tests"] = tests.get("result")
        evidence.extend(tests.get("evidence") or [])
        explained = explain_code(db_path, target, limit=limit)
        bundle["explain_code"] = explained.get("result")
        evidence.extend(explained.get("evidence") or [])
        graph = check_import_graph(db_path, limit=limit)
        bundle["import_graph"] = {
            "ok": graph.get("result", {}).get("ok"),
            "broken_count": graph.get("result", {}).get("broken_count"),
        }
        syntax = check_python_syntax(db_path, limit=limit)
        bundle["syntax"] = {
            "checked": syntax.get("result", {}).get("checked"),
            "error_count": syntax.get("result", {}).get("error_count"),
        }
        rel_graph = export_relation_graph(
            db_path, target, limit=min(limit, 30), fmt="mermaid"
        )
        bundle["relation_graph"] = {
            "format": rel_graph.get("result", {}).get("format"),
            "edge_count": rel_graph.get("result", {}).get("edge_count"),
            "graph": rel_graph.get("result", {}).get("graph"),
        }

    if revision:
        change = analyze_change_impact(db_path, revision=revision, limit=limit)
        bundle["change_impact"] = change.get("result")
        evidence.extend(change.get("evidence") or [])
        limitations.extend(change.get("limitations") or [])

    # de-dupe evidence lightly by type+symbol/source_ref
    seen: set[tuple] = set()
    unique_ev: list[dict[str, Any]] = []
    for item in evidence:
        key = (
            item.get("type"),
            item.get("symbol") or item.get("source_ref") or item.get("source"),
            item.get("status"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_ev.append(item)

    return make_envelope(
        status="success" if target or revision else "partial",
        repository=repository,
        result={"bundle": bundle},
        evidence=unique_ev[: limit * 3],
        limitations=limitations
        + ([] if (target or revision) else ["Provide target and/or revision for a full bundle"]),
    )


def render_evidence_report(
    db_path: Path,
    *,
    target: str | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Render a Markdown evidence report from an export bundle (Studio-lite)."""
    payload = export_evidence_bundle(
        db_path, target=target, revision=revision, limit=limit
    )
    if payload["status"] == "failed":
        return payload

    bundle = (payload.get("result") or {}).get("bundle") or {}
    repo = payload.get("repository") or {}
    lines: list[str] = [
        "# Witnis evidence report",
        "",
        f"- Repository: `{repo.get('name')}`",
        f"- Root: `{repo.get('root_path')}`",
        f"- Revision: `{repo.get('revision')}`",
    ]
    if target:
        lines.append(f"- Target: `{target}`")
    if revision:
        lines.append(f"- Change revision: `{revision}`")
    lines.append("")

    overview = bundle.get("overview") or {}
    if overview:
        lines.extend(
            [
                "## Overview",
                "",
                f"- Files: {overview.get('files')}",
                f"- Symbols: {overview.get('symbols')}",
                "",
            ]
        )

    explained = bundle.get("explain_code") or {}
    snippet = explained.get("snippet") or []
    if snippet:
        lines.extend(["## Snippet", "", "```"])
        for row in snippet[:40]:
            lines.append(f"{row.get('line')}: {row.get('text')}")
        lines.extend(["```", ""])

    impact = bundle.get("impact") or {}
    direct = impact.get("direct") or []
    if direct:
        lines.extend(["## Direct impact", ""])
        for edge in direct[:20]:
            lines.append(
                f"- `{edge.get('relation_type')}` "
                f"{edge.get('source')} → {edge.get('target')} "
                f"({edge.get('status', 'derived')})"
            )
        lines.append("")

    tests = (bundle.get("related_tests") or {}).get("tests") or []
    if tests:
        lines.extend(["## Related tests", ""])
        for t in tests[:20]:
            lines.append(
                f"- `{t.get('name')}` in `{t.get('file_path')}` ({t.get('reason')})"
            )
        lines.append("")

    change = bundle.get("change_impact") or {}
    hunk_syms = change.get("symbols_in_hunks") or []
    if hunk_syms:
        lines.extend(["## Symbols in change hunks", ""])
        for sym in hunk_syms[:20]:
            lines.append(
                f"- `{sym.get('name')}` @ `{sym.get('file_path')}:"
                f"{sym.get('start_line')}`"
            )
        lines.append("")

    evidence = payload.get("evidence") or []
    if evidence:
        lines.extend(["## Evidence", ""])
        for item in evidence[:30]:
            lines.append(
                f"- [{item.get('status')}] `{item.get('type')}` "
                f"{item.get('symbol') or item.get('source_ref') or item.get('source') or ''}"
            )
        lines.append("")

    limitations = payload.get("limitations") or []
    if limitations:
        lines.extend(["## Limitations", ""])
        for lim in limitations:
            lines.append(f"- {lim}")
        lines.append("")

    markdown = "\n".join(lines)
    # Minimal HTML twin for Studio-lite previews.
    html_body = (
        markdown.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Witnis evidence report</title>"
        "<style>body{font-family:ui-sans-serif,system-ui,sans-serif;max-width:880px;"
        "margin:2rem auto;padding:0 1rem;line-height:1.45}"
        "pre{background:#f6f8fa;padding:0.75rem;overflow:auto}</style>"
        "</head><body><pre>"
        f"{html_body}</pre></body></html>"
    )
    return make_envelope(
        status=payload.get("status", "success"),
        repository=repo,
        result={
            "markdown": markdown,
            "html": html,
            "bundle": bundle,
        },
        evidence=evidence,
        limitations=list(limitations)
        + [
            "Markdown/HTML reports are derived views of export_evidence_bundle",
            "HTML is a preformatted mirror of Markdown (not a full Studio UI)",
        ],
    )


def list_commits(db_path: Path, limit: int = 20) -> dict[str, Any]:
    """List persisted commits captured via explain_change."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        commits = store.list_commits(limit=limit) if repo else []
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={"commits": []},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    return make_envelope(
        status="success" if commits else "partial",
        repository=_repo_meta(repo),
        result={"commits": commits, "count": len(commits)},
        evidence=[
            {
                "type": "commit",
                "status": "observed",
                "hash": c.get("hash"),
                "subject": c.get("subject"),
            }
            for c in commits[:10]
        ],
        limitations=[]
        if commits
        else ["No commits persisted yet. Run explain-change / change-impact first."],
    )


def list_index_snapshots(db_path: Path, limit: int = 20) -> dict[str, Any]:
    """List index snapshots recorded after each index run."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        snaps = store.list_index_snapshots(limit=limit) if repo else []
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={"snapshots": []},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    return make_envelope(
        status="success" if snaps else "partial",
        repository=_repo_meta(repo),
        result={"snapshots": snaps, "count": len(snaps)},
        evidence=[
            {
                "type": "index_snapshot",
                "status": "observed",
                "captured_at": s.get("captured_at"),
                "files": s.get("files"),
                "symbols": s.get("symbols"),
            }
            for s in snaps[:10]
        ],
        limitations=[] if snaps else ["No index snapshots recorded yet"],
    )


def repo_status(db_path: Path) -> dict[str, Any]:
    """Aggregate overview + health + latest verification + latest snapshot."""
    overview = repo_overview(db_path)
    if overview["status"] == "failed":
        return overview
    health = check_index_health(db_path)
    snaps = list_index_snapshots(db_path, limit=3)
    from witnis.core.verify import get_verification_report, list_verification_runs

    runs = list_verification_runs(db_path, limit=3)
    report = get_verification_report(db_path)
    tests = list_test_results(db_path, limit=5)
    return make_envelope(
        status="success",
        repository=overview.get("repository"),
        result={
            "overview": overview.get("result"),
            "health": health.get("result"),
            "snapshots": (snaps.get("result") or {}).get("snapshots") or [],
            "verification_runs": (runs.get("result") or {}).get("runs") or [],
            "test_results": (tests.get("result") or {}).get("results") or [],
            "last_verification_state": (report.get("result") or {}).get("state"),
        },
        evidence=(overview.get("evidence") or [])[:5]
        + (health.get("evidence") or [])[:3],
        limitations=[
            "Status is an aggregate convenience view for agents",
            *(health.get("limitations") or [])[:2],
        ],
    )


def list_test_results(db_path: Path, limit: int = 50) -> dict[str, Any]:
    """List persisted verification step/test results."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        rows = store.list_test_results(limit=limit) if repo else []
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={"results": []},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    return make_envelope(
        status="success" if rows else "partial",
        repository=_repo_meta(repo),
        result={"results": rows, "count": len(rows)},
        evidence=[
            {
                "type": "test_result",
                "status": r.get("status"),
                "step_id": r.get("step_id"),
                "run_id": r.get("run_id"),
            }
            for r in rows[:20]
        ],
        limitations=[]
        if rows
        else ["No test/verification step results persisted yet"],
    )


def export_relation_graph(
    db_path: Path,
    target: str,
    *,
    limit: int = 40,
    fmt: str = "mermaid",
) -> dict[str, Any]:
    """Export a neighborhood graph around a symbol as Mermaid or DOT."""
    impact = analyze_impact(db_path, target, limit=limit)
    if impact["status"] == "failed":
        return impact
    traced = trace_symbol(db_path, target, limit=limit)
    edges: list[dict[str, Any]] = []
    edges.extend(impact.get("result", {}).get("direct") or [])
    edges.extend(traced.get("result", {}).get("calls") or [])
    edges.extend(traced.get("result", {}).get("called_by") or [])
    edges.extend(traced.get("result", {}).get("references") or [])
    # de-dupe
    seen: set[tuple] = set()
    unique: list[dict[str, Any]] = []
    for e in edges:
        key = (e.get("source"), e.get("target"), e.get("relation_type"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)
    unique = unique[:limit]

    def _nid(label: str) -> str:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in label)[:60]
        return cleaned or "node"

    if fmt == "dot":
        lines = ["digraph witnis {", '  rankdir="LR";']
        for e in unique:
            src = _nid(str(e.get("source") or "?"))
            tgt = _nid(str(e.get("target") or "?"))
            rel = str(e.get("relation_type") or "rel")
            lines.append(f'  "{src}" -> "{tgt}" [label="{rel}"];')
        lines.append("}")
        text = "\n".join(lines)
    else:
        lines = ["flowchart LR"]
        for e in unique:
            src = _nid(str(e.get("source") or "?"))
            tgt = _nid(str(e.get("target") or "?"))
            rel = str(e.get("relation_type") or "rel")
            src_label = str(e.get("source") or "?").replace('"', "'")
            tgt_label = str(e.get("target") or "?").replace('"', "'")
            lines.append(
                f'  {src}["{src_label}"] -->|{rel}| {tgt}["{tgt_label}"]'
            )
        text = "\n".join(lines)

    return make_envelope(
        status="success" if unique else "partial",
        repository=impact.get("repository"),
        result={
            "format": "dot" if fmt == "dot" else "mermaid",
            "graph": text,
            "edge_count": len(unique),
            "target": target,
        },
        evidence=(impact.get("evidence") or [])[:10],
        limitations=[
            "Graph is a neighborhood projection from impact/trace edges",
            "Node labels may collide after identifier sanitization",
        ],
    )


def refresh_index(db_path: Path) -> dict[str, Any]:
    """Incremental re-index of the repository already stored in the DB."""
    from witnis.core.index import index_repository

    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
    finally:
        store.close()
    if repo is None:
        return make_envelope(
            status="failed",
            repository=None,
            result={},
            limitations=["Index is empty. Run: witnis index <path>"],
        )
    root = Path(repo["root_path"])
    stats = index_repository(root, db_path, incremental=True)
    freshness = refresh_evidence(db_path)
    return make_envelope(
        status="success",
        repository=_repo_meta(repo),
        result={
            "files": stats.files,
            "symbols": stats.symbols,
            "updated_files": stats.updated_files,
            "skipped_unchanged": stats.skipped_unchanged,
            "removed_files": stats.removed_files,
            "db_path": stats.db_path,
            "evidence_marked_stale": (freshness.get("result") or {}).get(
                "marked_stale", 0
            ),
        },
        evidence=[
            {
                "type": "index_refresh",
                "status": "observed",
                "updated_files": stats.updated_files,
                "skipped_unchanged": stats.skipped_unchanged,
            }
        ],
        limitations=["Refresh is incremental only; use witnis index --full for rebuild"],
    )


def refresh_evidence(db_path: Path, limit: int = 500) -> dict[str, Any]:
    """Mark persisted evidence stale when watched file hashes changed."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={"marked_stale": 0, "checked": 0},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        repo_id = int(repo["id"])
        hashes = store.file_hashes(repo_id)
        rows = store.find_evidence(limit=limit)
        stale_ids: list[int] = []
        for row in rows:
            if row.get("status") == "stale":
                continue
            payload = row.get("payload") or {}
            watched = payload.get("watched_hashes") or {}
            path = row.get("path") or payload.get("path") or payload.get("file")
            content_hash = payload.get("content_hash")
            changed = False
            if watched:
                for p, old in watched.items():
                    cur = hashes.get(str(p))
                    if cur is None or cur != old:
                        changed = True
                        break
            elif path and content_hash:
                cur = hashes.get(str(path))
                if cur is None or cur != content_hash:
                    changed = True
            elif path and str(path) not in hashes:
                changed = True
            if changed and row.get("id") is not None:
                stale_ids.append(int(row["id"]))
        marked = store.mark_evidence_status(stale_ids, "stale")
    finally:
        store.close()
    return make_envelope(
        status="success",
        repository=_repo_meta(repo),
        result={
            "checked": len(rows),
            "marked_stale": marked,
            "stale_ids": stale_ids[:50],
        },
        evidence=[
            {
                "type": "evidence_refresh",
                "status": "observed",
                "marked_stale": marked,
            }
        ],
        limitations=[
            "Only evidence with path/content_hash or watched_hashes can be marked stale",
        ],
    )


def ingest_runtime_traces(
    db_path: Path,
    trace_path: Path,
    *,
    limit: int = 5000,
) -> dict[str, Any]:
    """Ingest optional JSONL runtime call traces and fuse into relations + evidence."""
    from witnis.core.runtime import load_runtime_trace_file
    from witnis.core.security import assert_path_in_root

    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        root = Path(repo["root_path"])
        path = Path(trace_path)
        # Allow traces inside repo or under .witnis next to the db
        try:
            assert_path_in_root(root.resolve(), path.resolve())
        except Exception:
            db_root = db_path.parent.resolve()
            try:
                assert_path_in_root(db_root, path.resolve())
            except Exception as exc:
                return make_envelope(
                    status="failed",
                    repository=_repo_meta(repo),
                    result={},
                    limitations=[f"Trace path outside sandbox: {exc}"],
                )
        if not path.is_file():
            return make_envelope(
                status="failed",
                repository=_repo_meta(repo),
                result={},
                limitations=[f"Trace file not found: {path}"],
            )
        events = load_runtime_trace_file(path, limit=limit)
        edges: list[dict[str, Any]] = []
        evidence_items: list[dict[str, Any]] = []
        for ev in events:
            edges.append(
                {
                    "source": ev["caller"],
                    "target": ev["callee"],
                    "relation_type": "calls",
                    "status": "observed",
                    "start_line": None,
                }
            )
            evidence_items.append(
                {
                    "type": "runtime_trace",
                    "status": "observed",
                    "source_ref": ev["callee"],
                    "path": None,
                    "caller": ev["caller"],
                    "callee": ev["callee"],
                    "count": ev.get("count"),
                    "trace_file": str(path),
                }
            )
        added = store.append_relations(int(repo["id"]), edges)
        store.insert_evidence_items(int(repo["id"]), evidence_items)
    finally:
        store.close()

    return make_envelope(
        status="success" if events else "partial",
        repository=_repo_meta(repo),
        result={
            "trace_path": str(path.resolve()),
            "accepted": len(events),
            "relations_added": added,
            "evidence_added": len(evidence_items),
        },
        evidence=evidence_items[:20],
        limitations=[
            "Runtime traces are optional and schema-flexible (caller/callee or from/to)",
            "Trace edges are observed facts fused into the static relation graph",
        ]
        if events
        else ["No usable call events found in the trace file"],
    )


def scan_secrets(db_path: Path, limit: int = 50) -> dict[str, Any]:
    """Scan indexed text files for secret-like assignments and sensitive paths."""
    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        rows = store.conn.execute(
            "SELECT path FROM files WHERE repo_id = ? ORDER BY path",
            (repo["id"],),
        ).fetchall()
        paths = [str(r["path"]) for r in rows]
    finally:
        store.close()

    root = Path(repo["root_path"])
    findings: list[dict[str, Any]] = []
    sensitive_paths: list[str] = []
    scanned = 0
    for rel in paths:
        if is_sensitive_path(rel):
            sensitive_paths.append(rel)
        suffix = Path(rel).suffix.lower()
        if suffix not in {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".env", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".txt", ".md"}:
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        for hit in scan_text_for_secrets(text, path=rel):
            findings.append(hit)
            if len(findings) >= limit:
                break
        if len(findings) >= limit:
            break

    return make_envelope(
        status="success" if not findings and not sensitive_paths else "partial",
        repository=_repo_meta(repo),
        result={
            "scanned_files": scanned,
            "findings": findings[:limit],
            "finding_count": len(findings),
            "sensitive_paths": sensitive_paths[:limit],
        },
        evidence=[
            {
                "type": "secret_scan",
                "status": "verified" if not findings else "uncertain",
                "finding_count": len(findings),
                "sensitive_path_count": len(sensitive_paths),
            }
        ]
        + [
            {
                "type": "secret_finding",
                "status": "uncertain",
                "path": f.get("path"),
                "line": f.get("line"),
                "preview": f.get("preview"),
            }
            for f in findings[:10]
        ],
        limitations=[
            "Heuristic scan only; does not prove secrets are real credentials",
            "Values are redacted in evidence previews",
        ],
    )


def query_lsp(
    db_path: Path,
    name: str,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    """Jedi LSP enrichment with index-backed fallback (always usable post-index)."""
    from witnis.core.lsp_python import (
        index_definitions,
        index_references,
        lsp_available,
        lsp_definitions,
        lsp_references,
        pyright_available,
        pyright_diagnostics,
    )

    store = _open_store(db_path)
    try:
        overview = store.overview()
        repo = overview.get("repository")
        if repo is None:
            return make_envelope(
                status="failed",
                repository=None,
                result={},
                limitations=["Index is empty. Run: witnis index <path>"],
            )
        root = Path(repo["root_path"])
        jedi_defs = lsp_definitions(root, name, limit=limit)
        jedi_refs = lsp_references(root, name, limit=limit * 2)
        idx_defs = index_definitions(store, name, limit=limit)
        idx_refs = index_references(store, name, limit=limit * 2)

        definitions = list(jedi_defs.get("definitions") or [])
        if not definitions:
            definitions = list(idx_defs.get("definitions") or [])
        references = list(jedi_refs.get("references") or [])
        if not references:
            references = list(idx_refs.get("references") or [])

        def_paths = [str(d.get("path")) for d in definitions if d.get("path")]
        pyright = pyright_diagnostics(root, name, paths=def_paths, limit=limit)

        backends = []
        if jedi_defs.get("backend") and (jedi_defs.get("definitions") or jedi_refs.get("references")):
            backends.append("jedi")
        if (not jedi_defs.get("definitions") and idx_defs.get("definitions")) or (
            not jedi_refs.get("references") and idx_refs.get("references")
        ):
            backends.append("index")
        if pyright.get("available") and pyright.get("diagnostics") is not None and pyright_available():
            backends.append("pyright")
        if not backends and lsp_available():
            backends.append("jedi")
        if not backends:
            backends.append("index")
        backend = "+".join(backends)

        available = bool(
            definitions or references or lsp_available() or pyright_available()
        )
        status = (
            "success"
            if definitions or references
            else ("partial" if available else "failed")
        )
        limitations = []
        if not lsp_available():
            limitations.append(
                "Jedi not installed — using index backend. pip install 'witnis[lsp]'"
            )
        if not pyright_available():
            limitations.append(
                "Pyright optional — install Node pyright/basedpyright for diagnostics"
            )
        for note in (
            jedi_defs.get("limitation"),
            jedi_refs.get("limitation"),
            idx_defs.get("limitation"),
            idx_refs.get("limitation"),
            pyright.get("limitation"),
        ):
            if note and note not in limitations and not (definitions or references):
                limitations.append(note)
        return make_envelope(
            status=status,
            repository=_repo_meta(repo),
            result={
                "name": name,
                "backend": backend,
                "available": available,
                "definitions": definitions,
                "references": references,
                "diagnostics": pyright.get("diagnostics") or [],
            },
            evidence=[
                {
                    "type": "lsp_definition",
                    "status": "observed",
                    "path": d.get("path"),
                    "line": d.get("line"),
                    "name": d.get("name"),
                }
                for d in definitions[:10]
            ]
            + [
                {
                    "type": "lsp_reference",
                    "status": "observed",
                    "path": r.get("path"),
                    "line": r.get("line"),
                    "name": r.get("name"),
                }
                for r in references[:10]
            ]
            + [
                {
                    "type": "pyright_diagnostic",
                    "status": "observed",
                    "path": d.get("path"),
                    "line": d.get("line"),
                    "name": d.get("severity"),
                }
                for d in (pyright.get("diagnostics") or [])[:5]
            ],
            limitations=limitations
            or ["LSP enrichment may combine Jedi, index, and Pyright backends"],
        )
    finally:
        store.close()


def list_capabilities() -> dict[str, Any]:
    """Describe local CLI/MCP capabilities for agents (no DB required)."""
    cli = [
        "index",
        "refresh",
        "overview",
        "status",
        "search",
        "look",
        "up",
        "demo",
        "home",
        "browser-demo",
        "scene",
        "trace",
        "explain",
        "explain-change",
        "impact",
        "change-impact",
        "pr-gate",
        "loop-init",
        "related-tests",
        "tests",
        "evidence",
        "export-bundle",
        "report",
        "graph",
        "import-graph",
        "syntax",
        "doctor",
        "compare",
        "compare-worktree",
        "scan-secrets",
        "commits",
        "snapshots",
        "test-results",
        "plan-verify",
        "plan",
        "verify",
        "verification-report",
        "verification-history",
        "bench",
        "capabilities",
        "studio",
        "watch",
        "refresh-evidence",
        "ingest-traces",
        "compare-baselines",
        "baselines",
        "lsp",
    ]
    mcp = [
        "index",
        "look",
        "impact",
        "verify",
    ]
    mcp_experimental = [
        "repo_overview",
        "repo_status",
        "repo_search",
        "trace_symbol",
        "explain_code",
        "explain_change",
        "analyze_impact",
        "analyze_change_impact",
        "analyze_pr_impact",
        "run_pr_gate",
        "find_related_tests",
        "get_evidence",
        "export_evidence_bundle",
        "render_evidence_report",
        "export_relation_graph",
        "check_import_graph",
        "check_index_health",
        "check_python_syntax",
        "compare_revisions",
        "compare_worktree",
        "scan_secrets",
        "refresh_index",
        "list_commits",
        "list_index_snapshots",
        "list_test_results",
        "create_verification_plan",
        "run_verification",
        "get_verification_report",
        "list_verification_runs",
        "list_capabilities",
        "render_studio",
        "refresh_evidence",
        "ingest_runtime_traces",
        "query_lsp",
    ]
    stable_cli = [
        "index",
        "refresh",
        "overview",
        "status",
        "search",
        "look",
        "trace",
        "impact",
        "evidence",
        "plan-verify",
        "plan",
        "verify",
        "studio",
        "capabilities",
        "bench",
        "compare-baselines",
        "lsp",
    ]
    stable_mcp = ["index", "look", "impact", "verify"]
    return make_envelope(
        status="success",
        repository=None,
        result={
            "version": __import__("witnis").__version__,
            "contract": "stable",
            "cli_commands": cli,
            "mcp_tools": mcp,
            "mcp_experimental": mcp_experimental,
            "stable_cli_commands": stable_cli,
            "stable_mcp_tools": stable_mcp,
            "verify_requires": ["--execute", "WITNIS_ALLOW_VERIFY=1"],
        },
        evidence=[
            {
                "type": "capabilities",
                "status": "observed",
                "cli_count": len(cli),
                "mcp_count": len(mcp),
                "contract": "stable",
            }
        ],
        limitations=[
            "Capability list is declarative and may lag if tools are added mid-release",
            "stable_* lists are the v1 compatibility surface; other commands may evolve",
        ],
    )
