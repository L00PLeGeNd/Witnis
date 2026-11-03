from __future__ import annotations

import re
from pathlib import Path

from witnis.core.models import Symbol

_CLASS_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_][\w$]*)"
)
_FUNC_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w$]*)\s*\("
)
_CONST_FUNC_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][\w$]*)\s*=>"
)
_METHOD_RE = re.compile(
    r"(?m)^\s+(?:async\s+)?([A-Za-z_][\w$]*)\s*\([^)]*\)\s*\{"
)


def parse_js_source(source: str, *, rel_path: str) -> list[Symbol]:
    """Shallow JS/TS symbol extraction (regex; not a full parser)."""
    symbols: list[Symbol] = []
    lines = source.splitlines()

    def _line_at(match_start: int) -> int:
        # 1-based
        return source.count("\n", 0, match_start) + 1

    for m in _CLASS_RE.finditer(source):
        start = _line_at(m.start())
        symbols.append(
            Symbol(
                name=m.group(1),
                kind="class",
                file_path=rel_path,
                start_line=start,
                end_line=start,
            )
        )
    for m in _FUNC_RE.finditer(source):
        start = _line_at(m.start())
        symbols.append(
            Symbol(
                name=m.group(1),
                kind="function",
                file_path=rel_path,
                start_line=start,
                end_line=start,
            )
        )
    for m in _CONST_FUNC_RE.finditer(source):
        start = _line_at(m.start())
        symbols.append(
            Symbol(
                name=m.group(1),
                kind="function",
                file_path=rel_path,
                start_line=start,
                end_line=start,
            )
        )
    # Methods only when indented under a class-ish block (heuristic).
    in_class = False
    for i, line in enumerate(lines, start=1):
        if _CLASS_RE.match(line):
            in_class = True
            continue
        if in_class and line and not line[0].isspace() and not line.startswith("}"):
            # top-level resume
            if not line.startswith("}") and re.match(r"\S", line):
                in_class = False
        if not in_class:
            continue
        m = _METHOD_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in {"if", "for", "while", "switch", "catch"}:
            continue
        # find nearest preceding class
        class_name = None
        for j in range(i - 1, 0, -1):
            cm = _CLASS_RE.match(lines[j - 1])
            if cm:
                class_name = cm.group(1)
                break
        if not class_name:
            continue
        symbols.append(
            Symbol(
                name=f"{class_name}.{name}",
                kind="method",
                file_path=rel_path,
                start_line=i,
                end_line=i,
            )
        )
    return symbols


def parse_js_file(path: Path, *, rel_path: str) -> list[Symbol]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    return parse_js_source(source, rel_path=rel_path)
