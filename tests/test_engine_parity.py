"""Cross-engine contract: Python path vs optional Rust path on fixed fixtures.

When witnis._native is unavailable, Rust half is skipped — not failed.
When both run, symbol name sets must overlap above a Jaccard floor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from witnis.core.index import index_repository
from witnis.core.native import NATIVE_AVAILABLE, rust_index_repository
from witnis.core.security import redact_text, scan_text_for_secrets, shannon_entropy
from witnis.core.store import Store
from witnis.core.verify_isolate import build_container_command

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "mini_py"


def _symbol_names(db: Path) -> set[str]:
    store = Store(db)
    try:
        rows = store.conn.execute(
            "SELECT DISTINCT name FROM symbols WHERE name IS NOT NULL AND name != ''"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        store.close()


@pytest.mark.skipif(not FIXTURE.is_dir(), reason="mini_py fixture missing")
def test_python_index_has_core_symbols(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WITNIS_RUST_INDEX", "0")
    db = tmp_path / "py.sqlite"
    stats = index_repository(FIXTURE, db, incremental=False)
    assert stats.symbols >= 1
    names = _symbol_names(db)
    assert names, "python engine produced no symbols on mini_py"
    assert any("login" in n.lower() for n in names), names


@pytest.mark.skipif(not NATIVE_AVAILABLE, reason="witnis._native not built")
@pytest.mark.skipif(not FIXTURE.is_dir(), reason="mini_py fixture missing")
def test_python_rust_symbol_name_parity(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WITNIS_RUST_INDEX", "0")
    py_db = tmp_path / "py.sqlite"
    index_repository(FIXTURE, py_db, incremental=False)
    py_names = _symbol_names(py_db)

    rs_db = tmp_path / "rs.sqlite"
    rust_stats = rust_index_repository(FIXTURE, rs_db, incremental=False)
    assert rust_stats is not None
    rs_names = _symbol_names(rs_db)

    assert py_names, "python empty"
    assert rs_names, "rust empty"
    overlap = py_names & rs_names
    assert overlap, f"no shared symbols: py={sorted(py_names)[:20]} rs={sorted(rs_names)[:20]}"
    jaccard = len(overlap) / max(1, len(py_names | rs_names))
    assert jaccard >= 0.4, f"parity jaccard {jaccard:.2f} too low (py={len(py_names)} rs={len(rs_names)})"


def test_container_verify_command_builder(tmp_path: Path) -> None:
    cmd = build_container_command(
        ["C:/Python312/python.exe", "-m", "pytest", "-q"],
        cwd=tmp_path,
        runtime="docker",
        allow_network=False,
    )
    assert cmd[:6] == ["docker", "run", "--rm", "--network", "none", "--read-only"]
    joined = " ".join(cmd)
    assert "PYTHONPYCACHEPREFIX=/tmp/pycache" in joined
    assert ":/work:ro" in joined
    assert cmd[-4:] == ["python3", "-m", "pytest", "-q"]


def test_secret_scanner_known_tokens_and_entropy() -> None:
    sample = "export GH=ghp_1234567890abcdefghij1234567890abcdef\nAKIAIOSFODNN7EXAMPLE\n"
    redacted = redact_text(sample)
    assert "ghp_" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    hits = scan_text_for_secrets(sample, path="sample.env")
    kinds = {h["kind"] for h in hits}
    assert "github_token" in kinds
    assert "aws_access_key" in kinds
    assert shannon_entropy("ghp_1234567890abcdefghij1234567890abcdef") > 3.5
