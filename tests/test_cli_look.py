from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.index import index_repository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
runner = CliRunner()


def test_look_prints_witness_card(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["look", "login", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "login" in result.output
    assert "impact" in result.output
    assert "plan" in result.output


def test_plan_alias_accepts_positional_symbol(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["plan", "login", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "steps" in result.output
