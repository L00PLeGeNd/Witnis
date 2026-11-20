from __future__ import annotations

import re
from pathlib import Path

from witnis.core.models import Symbol

_CLASS_RE = re.compile(r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?class\s+([A-Za-z_][\w]*)")
_INTERFACE_RE = re.compile(r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?interface\s+([A-Za-z_][\w]*)")
_METHOD_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+([A-Za-z_][\w]*)\s*\("
)
_SKIP_METHODS = {"if", "for", "while", "switch", "catch", "return", "new", "class"}


def parse_java_file(path: Path, *, rel_path: str) -> list[Symbol]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    symbols: list[Symbol] = []
    for regex, kind in ((_CLASS_RE, "class"), (_INTERFACE_RE, "interface")):
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
    for m in _METHOD_RE.finditer(source):
        name = m.group(1)
        if name in _SKIP_METHODS:
            continue
        line = source.count("\n", 0, m.start()) + 1
        symbols.append(
            Symbol(
                name=name,
                kind="method",
                file_path=rel_path,
                start_line=line,
                end_line=line,
            )
        )
    return symbols
