from __future__ import annotations

import re
from pathlib import Path

from witnis.core.models import Symbol

_FUNC_RE = re.compile(
    r"(?m)^func\s+(?:\([^)]+\)\s+)?([A-Za-z_][\w]*)\s*\("
)
_TYPE_RE = re.compile(r"(?m)^type\s+([A-Za-z_][\w]*)\s+(?:struct|interface|func|[A-Za-z_])")
_CONST_RE = re.compile(r"(?m)^const\s+([A-Za-z_][\w]*)\s*=")
_VAR_RE = re.compile(r"(?m)^var\s+([A-Za-z_][\w]*)\s+")


def parse_go_file(path: Path, *, rel_path: str) -> list[Symbol]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    symbols: list[Symbol] = []
    for regex, kind in (
        (_TYPE_RE, "type"),
        (_FUNC_RE, "function"),
        (_CONST_RE, "const"),
        (_VAR_RE, "var"),
    ):
        for m in regex.finditer(source):
            line = source.count("\n", 0, m.start()) + 1
            symbols.append(
                Symbol(
                    name=m.group(1),
                    kind=kind,
                    file_path=rel_path,
                    start_line=line,
                    end_line=line,
                )
            )
    return symbols
