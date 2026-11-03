from __future__ import annotations

from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store
from witnis.core.tools import repo_overview

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_indexes_import_relation(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db)
    store = Store(db)
    try:
        rels = store.list_relations()
    finally:
        store.close()
    assert any(
        r["source"] == "app.py" and "auth" in r["target"] for r in rels
    ), rels


def test_overview_includes_relation_sample(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db)
    payload = repo_overview(db)
    assert payload["result"]["relation_sample_count"] >= 1
