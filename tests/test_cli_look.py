from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.index import index_repository

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "mini_py"
PETCLINIC = (
    ROOT
    / "benchmarks"
    / "ground-truth"
    / "corpora"
    / "checkouts"
    / "spring-petclinic"
)
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
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["impact", "login", "--db", str(db), "--limit", "1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert len(payload["result"]["direct"]) <= 1
    assert len(payload["result"]["transitive"]) <= 1


def test_impact_plain_prints_transitive_edges(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    js = runner.invoke(app, ["impact", "login", "--db", str(db)])
    payload = json.loads(js.output)
    if not payload["result"].get("transitive"):
        pytest.skip("fixture login has no transitive edges")
    plain = runner.invoke(app, ["impact", "login", "--db", str(db), "--plain"])
    assert plain.exit_code == 0, plain.output
    assert "Transitive\t" in plain.output


def test_impact_cli_petclinic_person_names_controllers(tmp_path: Path) -> None:
    if not PETCLINIC.is_dir():
        pytest.skip("clone spring-petclinic per benchmarks/ground-truth/blind-pack/CLONE.md")
    db = tmp_path / "petclinic.sqlite"
    index_repository(PETCLINIC, db, incremental=False)
    js = runner.invoke(app, ["impact", "Person", "--db", str(db)])
    assert js.exit_code == 0, js.output
    blob = js.output
    for name in ("OwnerController", "PetController", "VisitController"):
        assert name in blob, name
    plain = runner.invoke(app, ["impact", "Person", "--db", str(db), "--plain"])
    assert plain.exit_code == 0, plain.output
    look = runner.invoke(app, ["look", "Person", "--db", str(db)])
    assert look.exit_code == 0, look.output
    for name in ("OwnerController", "PetController", "VisitController"):
        assert name in plain.output, name
        assert name in look.output, name


def test_plan_alias_accepts_positional_symbol(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    result = runner.invoke(app, ["plan", "login", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "steps" in result.output
