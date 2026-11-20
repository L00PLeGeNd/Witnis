from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.index import index_repository
from witnis.core.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
runner = CliRunner()


def test_index_repository_finds_login(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    stats = index_repository(FIXTURE, db)
    assert stats.files >= 2
    assert stats.symbols >= 3

    store = Store(db)
    try:
        hits = store.search("login")
    finally:
        store.close()

    assert hits
    names = {h["name"] for h in hits}
    assert "AuthService.login" in names or any("login" in n for n in names)
    login_hits = [h for h in hits if "login" in h["name"]]
    assert login_hits[0]["file_path"].endswith("auth.py")
    assert login_hits[0]["start_line"] >= 1


def test_cli_index_overview_search(tmp_path: Path) -> None:
    db = tmp_path / "cli.sqlite"
    result = runner.invoke(app, ["index", str(FIXTURE), "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "symbols=" in result.output

    result = runner.invoke(app, ["overview", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "files=" in result.output
    assert "symbols=" in result.output

    result = runner.invoke(app, ["search", "AuthService", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "AuthService" in result.output
