from __future__ import annotations

from pathlib import Path

import pytest

from witnis.core.index import index_repository
from witnis.core.tools import repo_overview, repo_search

HARNIS = Path(r"C:\Users\Ibiza\Desktop\IT\Harnis")


@pytest.mark.skipif(not (HARNIS / "src").exists(), reason="Harnis checkout not present")
def test_index_harnis_repo_smoke(tmp_path: Path) -> None:
    db = tmp_path / "harnis.sqlite"
    stats = index_repository(HARNIS, db, incremental=False)
    assert stats.files >= 5
    assert stats.symbols >= 10
    overview = repo_overview(db)
    assert overview["status"] == "success"
    hits = repo_search(db, "harnis")
    assert hits["status"] in {"success", "partial"}
