"""Seam: git subprocess decode uses UTF-8 (Windows GBK hosts)."""

from __future__ import annotations

from pathlib import Path

from witnis.core import gitinfo


def test_run_git_accepts_utf8_bytes(monkeypatch, tmp_path: Path) -> None:
    class FakeProc:
        returncode = 0
        stdout = "café\n"
        stderr = ""

    def fake_run(*args, **kwargs):
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "replace"
        return FakeProc()

    monkeypatch.setattr(gitinfo.subprocess, "run", fake_run)
    proc = gitinfo._run_git(tmp_path, "status")
    assert proc.stdout.strip() == "café"
