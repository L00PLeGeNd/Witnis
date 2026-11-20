from __future__ import annotations

from pathlib import Path

import pytest

from witnis.core.discover import iter_source_files
from witnis.core.security import assert_path_in_root, is_sensitive_path, redact_text


def test_redact_text_masks_secrets() -> None:
    text = "api_key=sk-abc password: hunter2"
    out = redact_text(text)
    assert "sk-abc" not in out
    assert "hunter2" not in out
    assert "***REDACTED***" in out


def test_sensitive_path_detection() -> None:
    assert is_sensitive_path(".env")
    assert is_sensitive_path("secrets/token.pem")
    assert not is_sensitive_path("auth.py")


def test_assert_path_in_root(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    inside = root / "a.py"
    inside.write_text("x=1\n", encoding="utf-8")
    assert assert_path_in_root(root, inside) == inside.resolve()
    outside = tmp_path / "other.py"
    outside.write_text("y=1\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        assert_path_in_root(root, outside)


def test_discover_skips_env_file(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    files = [p.name for p in iter_source_files(root)]
    assert files == ["ok.py"]
