from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from witnis.cli import app

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
runner = CliRunner()


def test_up_indexes_and_looks(tmp_path: Path) -> None:
    db = tmp_path / "up.sqlite"
    result = runner.invoke(
        app,
        ["up", str(FIXTURE), "--symbol", "login", "--db", str(db)],
    )
    assert result.exit_code == 0, result.output
    assert "index" in result.output
    assert "login" in result.output
    assert "impact" in result.output
