from __future__ import annotations

import math
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

# Known high-confidence token formats (GitHub PAT/OAuth, AWS AKIA, Slack xox*, OpenAI/Anthropic sk-*, JWT, Private Key)
_KNOWN_TOKEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,255}\b")),
    ("github_fine_grained_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,255}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,120}\b")),
    ("api_secret_sk", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,200}\b")),
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
]


def shannon_entropy(token: str) -> float:
    """Compute Shannon entropy (bits per character) of a string."""
    if not token:
        return 0.0
    length = len(token)
    counts: dict[str, int] = {}
    for ch in token:
        counts[ch] = counts.get(ch, 0) + 1
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


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
    """Redact obvious secret assignments and known token formats in free text."""

    def _sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}=***REDACTED***"

    out = _SECRET_VALUE_RE.sub(_sub, text)
    for kind, pattern in _KNOWN_TOKEN_PATTERNS:
        if kind == "private_key_header":
            out = pattern.sub("-----BEGIN ***REDACTED*** PRIVATE KEY-----", out)
        else:
            out = pattern.sub(f"***REDACTED:{kind}***", out)
    return out


def scan_text_for_secrets(text: str, *, path: str = "") -> list[dict]:
    """Return redacted secret-like assignment and known-token hits in text."""
    hits: list[dict] = []
    seen_lines: set[tuple[int, str]] = set()
    for match in _SECRET_VALUE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        val = match.group(2).strip("'\"")
        seen_lines.add((line_no, match.group(1)))
        hits.append(
            {
                "path": path,
                "line": line_no,
                "kind": "assignment",
                "key": match.group(1),
                "entropy": round(shannon_entropy(val), 2),
                "preview": redact_text(match.group(0)),
            }
        )
    for kind, pattern in _KNOWN_TOKEN_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            if (line_no, kind) in seen_lines:
                continue
            seen_lines.add((line_no, kind))
            raw = match.group(0)
            hits.append(
                {
                    "path": path,
                    "line": line_no,
                    "kind": kind,
                    "key": kind,
                    "entropy": round(shannon_entropy(raw), 2),
                    "preview": redact_text(raw),
                }
            )
    return hits
