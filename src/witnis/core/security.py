from __future__ import annotations

import re
from pathlib import Path

SECRET_NAME_MARKERS = (
    ".env",
    "credentials",
    "secret",
    "id_rsa",
    ".pem",
    ".key",
)

_SECRET_VALUE_RE = re.compile(
    r"(?i)\b([\w-]*(?:api[_-]?key|token|secret|password)[\w-]*)\s*[:=]\s*"
    r"([^\s,;]+)"
)


def assert_path_in_root(root: Path, candidate: Path) -> Path:
    """Resolve candidate and ensure it stays inside root (symlink-safe-ish)."""
    root_r = root.resolve()
    cand_r = candidate.resolve()
    try:
        cand_r.relative_to(root_r)
    except ValueError as exc:
        raise PermissionError(
            f"Path escapes repository sandbox: {cand_r} not under {root_r}"
        ) from exc
    return cand_r


def is_sensitive_path(path: Path | str) -> bool:
    """True for likely secret filenames (not arbitrary path substrings)."""
    p = Path(path)
    name = p.name.lower()
    if name in {".env", ".env.local"}:
        return True
    # Only inspect the filename itself — full-path substring matches false-positive
    # on dirs like test_scan_secrets_* in pytest tmp paths.
    return any(marker in name for marker in SECRET_NAME_MARKERS)


def redact_text(text: str) -> str:
    """Redact obvious secret assignments in free text."""

    def _sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}=***REDACTED***"

    return _SECRET_VALUE_RE.sub(_sub, text)


def scan_text_for_secrets(text: str, *, path: str = "") -> list[dict]:
    """Return redacted secret-like assignment hits in text."""
    hits: list[dict] = []
    for match in _SECRET_VALUE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        hits.append(
            {
                "path": path,
                "line": line_no,
                "kind": "assignment",
                "key": match.group(1),
                "preview": redact_text(match.group(0)),
            }
        )
    return hits
