from __future__ import annotations

import re
from pathlib import Path

_IMPORT_FROM_RE = re.compile(
    r"""(?m)^import\s+(?:type\s+)?(?:[\w$\s{},*]+)\s+from\s+['"]([^'"]+)['"]"""
)
_IMPORT_SIDE_RE = re.compile(r"""(?m)^import\s+['"]([^'"]+)['"]""")
_REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
_EXPORT_FROM_RE = re.compile(
    r"""(?m)^export\s+.+\s+from\s+['"]([^'"]+)['"]"""
)
_EXTENDS_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)\s+extends\s+([A-Za-z_$][\w$.]*)"
)


def parse_js_imports(path: Path, *, rel_path: str) -> list[dict]:
    """Shallow JS/TS import/require/export-from edges."""
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    edges: list[dict] = []
    seen: set[tuple[str, str, int]] = set()

    def _add(target: str, line: int, relation_type: str = "imports") -> None:
        key = (target, relation_type, line)
        if key in seen:
            return
        seen.add(key)
        edges.append(
            {
                "source": rel_path,
                "target": target,
                "relation_type": relation_type,
                "status": "observed",
                "start_line": line,
            }
        )

    for m in _IMPORT_FROM_RE.finditer(source):
        _add(m.group(1), source.count("\n", 0, m.start()) + 1)
    for m in _IMPORT_SIDE_RE.finditer(source):
        _add(m.group(1), source.count("\n", 0, m.start()) + 1)
    for m in _EXPORT_FROM_RE.finditer(source):
        _add(m.group(1), source.count("\n", 0, m.start()) + 1, "exports_from")
    for m in _REQUIRE_RE.finditer(source):
        _add(m.group(1), source.count("\n", 0, m.start()) + 1, "requires")
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


_CALL_RE = re.compile(
    r"""(?P<recv>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\("""
)
_NEW_RE = re.compile(r"""\bnew\s+(?P<cls>[A-Za-z_$][\w$]*)\s*\(""")
_KEYWORD_CALLEES = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "function",
    "return",
    "typeof",
    "await",
    "import",
    "export",
    "class",
    "const",
    "let",
    "var",
}


def parse_js_calls(path: Path, *, rel_path: str) -> list[dict]:
    """Shallow JS/TS call edges (regex; not scope-accurate)."""
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    edges: list[dict] = []
    seen: set[tuple[str, str, int]] = set()

    def _add(target: str, line: int) -> None:
        leaf = target.split(".")[-1]
        if leaf in _KEYWORD_CALLEES:
            return
        key = (target, line)
        if key in seen:
            return
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

    for m in _NEW_RE.finditer(source):
        _add(m.group("cls"), source.count("\n", 0, m.start()) + 1)
    for m in _CALL_RE.finditer(source):
        recv = m.group("recv")
        # Skip constructor already captured via `new`
        before = source[max(0, m.start() - 4) : m.start()]
        if before.rstrip().endswith("new"):
            continue
        _add(recv, source.count("\n", 0, m.start()) + 1)
    return edges
