from __future__ import annotations

import re
from pathlib import Path

_IMPORT_RE = re.compile(r"(?m)^import\s+(static\s+)?([A-Za-z_][\w.]*)\s*;")
_EXTENDS_RE = re.compile(
    r"(?m)class\s+([A-Za-z_][\w]*)\s+extends\s+([A-Za-z_][\w.]*)"
)
_CALL_RE = re.compile(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\(")
_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "class",
    "super",
    "this",
    "System",
}


def parse_java_imports(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for m in _IMPORT_RE.finditer(source):
        target = m.group(2)
        line = source.count("\n", 0, m.start()) + 1
        key = (target, line)
        if key in seen:
            continue
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
    for m in _EXTENDS_RE.finditer(source):
        line = source.count("\n", 0, m.start()) + 1
        edges.append(
            {
                "source": f"{rel_path}:{m.group(1)}",
                "target": m.group(2),
                "relation_type": "inherits",
                "status": "observed",
                "start_line": line,
            }
        )
    return edges


def parse_java_calls(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for m in _CALL_RE.finditer(source):
        target = m.group(1)
        leaf = target.split(".")[-1]
        if leaf in _KEYWORDS or target in _KEYWORDS:
            continue
        before = source[max(0, m.start() - 4) : m.start()]
        if before.rstrip().endswith("new"):
            # still record constructor-ish as calls with class name
            pass
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
