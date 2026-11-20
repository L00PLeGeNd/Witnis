from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.index import index_repository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
runner = CliRunner()


def test_home_resolves_packaged_page_and_assets() -> None:
    result = runner.invoke(app, ["home", "--no-open"])
    assert result.exit_code == 0, result.output
    page = Path(result.output.strip())
    assert page.is_file()
    assets = page.parent / "assets"
    for name in (
        "witnis-masthead.svg",
        "blast-radius.svg",
        "trusted-agent-loop.svg",
    ):
        assert (assets / name).is_file(), name


def test_look_prints_witness_card(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["look", "login", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "login" in result.output
    assert "impact" in result.output
    assert "plan" in result.output


def test_impact_cli_honors_limit(tmp_path: Path) -> None:
    import json

    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["impact", "login", "--db", str(db), "--limit", "1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert len(payload["result"]["direct"]) <= 1
    assert len(payload["result"]["transitive"]) <= 1


def test_plan_alias_accepts_positional_symbol(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["plan", "login", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "steps" in result.output
