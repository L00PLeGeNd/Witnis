from __future__ import annotations

import re
from pathlib import Path

_IMPORT_BLOCK_RE = re.compile(r"(?ms)^import\s*\((.*?)\)")
_IMPORT_SINGLE_RE = re.compile(r'(?m)^import\s+(?:[A-Za-z_]\w*\s+)?\"([^\"]+)\"')
_IMPORT_LINE_RE = re.compile(r'(?m)^\s*(?:[A-Za-z_]\w*\s+)?\"([^\"]+)\"')
_CALL_RE = re.compile(
    r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\("
)
_KEYWORDS = {
    "if",
    "for",
    "switch",
    "select",
    "return",
    "go",
    "defer",
    "func",
    "type",
    "range",
    "make",
    "new",
    "append",
    "len",
    "cap",
    "close",
    "copy",
    "delete",
    "panic",
    "recover",
}


def parse_go_imports(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, int]] = set()

    def _add(target: str, line: int) -> None:
        key = (target, line)
        if key in seen:
            return
        seen.add(key)
        edges.append(
            {
                "source": rel_path,
                "target": target,
                "relation_type": "imports",
                "status": "observed",
                "start_line": line,
            }
        )

    for m in _IMPORT_BLOCK_RE.finditer(source):
        block = m.group(1)
        base = m.start(1)
        for im in _IMPORT_LINE_RE.finditer(block):
            line = source.count("\n", 0, base + im.start()) + 1
            _add(im.group(1), line)
    for m in _IMPORT_SINGLE_RE.finditer(source):
        # skip if already inside a block match region roughly
        line = source.count("\n", 0, m.start()) + 1
        _add(m.group(1), line)
    return edges


def parse_go_calls(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for m in _CALL_RE.finditer(source):
        target = m.group(1)
        leaf = target.split(".")[-1]
        if leaf in _KEYWORDS:
            continue
        line = source.count("\n", 0, m.start()) + 1
        key = (target, line)
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                "source": f"{rel_path}:module",
                "target": target,
                "relation_type": "calls",
                "status": "derived",
                "start_line": line,
            }
        )
    return edges
