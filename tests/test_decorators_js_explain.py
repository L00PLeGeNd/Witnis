from __future__ import annotations

import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import explain_change, explain_code, repo_search

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PY = ROOT / "fixtures" / "mini_py"
FIXTURE_JS = ROOT / "fixtures" / "mini_js"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_indexes_decorator_edges(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_PY, db, incremental=False)
    store = Store(db)
    try:
        edges = store.find_relations(relation_type="decorated_by", limit=50)
    finally:
        store.close()
    assert any(
        "AuthService.login" in str(e.get("source")) and e.get("target") == "audit"
        for e in edges
    ), edges


def test_indexes_typescript_symbols(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE_JS, db, incremental=False)
    hits = repo_search(db, "TokenService")
    names = {h["name"] for h in hits["result"]["matches"]}
    assert "TokenService" in names
    # methods or sibling functions from the same fixture
    all_hits = repo_search(db, "verifyToken")
    all_names = names | {h["name"] for h in all_hits["result"]["matches"]}
    assert "verifyToken" in all_names or any(
        n.startswith("TokenService.") for n in all_names
    )


def test_explain_code_reads_historical_blob(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return 'old'\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "old")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    (repo / "auth.py").write_text(
        "class AuthService:\n    def login(self):\n        return 'new'\n",
        encoding="utf-8",
    )
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = explain_code(db, "AuthService.login", revision=head)
    assert payload["result"]["snippet_source"] == "historical_blob"
    texts = "\n".join(row["text"] for row in payload["result"]["snippet"])
    assert "old" in texts
    assert "new" not in texts


def test_explain_change_persists_commit(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "add f")
    db = tmp_path / "index.sqlite"
    index_repository(repo, db, incremental=False)
    payload = explain_change(db, revision="HEAD")
    commit_hash = payload["result"]["commit"]["hash"]
    store = Store(db)
    try:
        rid = int(store.overview()["repository"]["id"])
        saved = store.get_commit(rid, commit_hash)
    finally:
        store.close()
    assert saved is not None
    assert saved["subject"] == "add f"
