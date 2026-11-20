from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def make_envelope(
    *,
    status: str,
    repository: dict[str, Any] | None,
    result: Any,
    evidence: list[dict[str, Any]] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Structured Witnis response: facts + evidence + limitations."""
    return {
        "status": status,
        "repository": repository,
        "result": result,
        "evidence": evidence or [],
        "limitations": limitations or [],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def symbol_evidence(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "symbol",
        "status": "observed",
        "file": hit.get("file_path"),
        "symbol": hit.get("name"),
        "kind": hit.get("kind"),
        "lines": [hit.get("start_line"), hit.get("end_line")],
    }
