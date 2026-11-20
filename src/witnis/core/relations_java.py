"""Java relation extraction: imports/inherits/implements, Spring-style injects,
typed calls, and signature uses_type (params/returns).

Depth goal: move beyond name-only call sites toward DI + interface binding edges
that support impact analysis on Spring Boot–style trees. Not a full Java compiler.
"""

from __future__ import annotations

import re
from pathlib import Path

_IMPORT_RE = re.compile(r"(?m)^import\s+(static\s+)?([A-Za-z_][\w.]*)\s*;")
_EXTENDS_RE = re.compile(
    r"(?m)class\s+([A-Za-z_][\w]*)\s+extends\s+([A-Za-z_][\w.]*)"
)
_IMPLEMENTS_RE = re.compile(
    r"(?m)class\s+([A-Za-z_][\w]*)\b[^{;]*?\bimplements\s+([^{]+)\{"
)
_CLASS_HEADER_RE = re.compile(
    r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?"
    r"(class|interface)\s+([A-Za-z_][\w]*)"
)
_FIELD_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private|static|final|volatile|transient|\s)+"
    r"([A-Za-z_][\w.]*(?:<[^;]+>)?)\s+([A-Za-z_][\w]*)\s*[;=]"
)
_AUTOWIRED_RE = re.compile(r"@Autowired\b|@Inject\b|@Resource\b")
_CTOR_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private)\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*\{"
)
_METHOD_HEADER_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+"
    r"([A-Za-z_][\w]*)\s*\([^;]*\)\s*\{"
)
_METHOD_SIG_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private|static|final|synchronized|\s)+"
    r"([A-Za-z_][\w.]*(?:<[^>\n]+>)?(?:\[\])?)\s+"
    r"([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\{"
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
# Skip ubiquitous JDK / collection names so uses_type stays blast-radius signal.
_USES_TYPE_SKIP = _KEYWORDS | {
    "void",
    "int",
    "long",
    "boolean",
    "byte",
    "short",
    "char",
    "float",
    "double",
    "String",
    "Integer",
    "Long",
    "Boolean",
    "Object",
    "Class",
    "List",
    "Map",
    "Set",
    "Optional",
    "Collection",
    "Iterable",
    "Override",
    "Deprecated",
}


def _line_at(source: str, pos: int) -> int:
    return source.count("\n", 0, pos) + 1


def _simple_type(type_expr: str) -> str:
    """Strip generics/arrays/packages → simple type name."""
    t = type_expr.strip()
    if "<" in t:
        t = t.split("<", 1)[0].strip()
    t = t.rstrip("[]").strip()
    if "." in t:
        t = t.rsplit(".", 1)[-1]
    return t


def _enclosing_type(source: str, pos: int) -> str | None:
    last: str | None = None
    for m in _CLASS_HEADER_RE.finditer(source):
        if m.start() > pos:
            break
        last = m.group(2)
    return last


def _enclosing_method(source: str, pos: int) -> str | None:
    """Best-effort: nearest method/ctor header before pos inside same type body."""
    best_pos = -1
    last: str | None = None
    for m in _METHOD_HEADER_RE.finditer(source):
        if m.start() > pos:
            break
        name = m.group(1)
        if name in _KEYWORDS:
            continue
        if m.start() >= best_pos:
            best_pos = m.start()
            last = name
    for m in _CTOR_RE.finditer(source):
        if m.start() > pos:
            break
        if m.start() >= best_pos:
            best_pos = m.start()
            last = m.group(1)
    return last


def _fields(source: str) -> list[tuple[str, str, int, bool]]:
    """Return (type_simple, field_name, line, injected)."""
    out: list[tuple[str, str, int, bool]] = []
    for m in _FIELD_RE.finditer(source):
        type_name = _simple_type(m.group(1))
        field = m.group(2)
        if type_name in _KEYWORDS or field in _KEYWORDS:
            continue
        # look back ~200 chars for injection annotations
        window = source[max(0, m.start() - 220) : m.start()]
        injected = bool(_AUTOWIRED_RE.search(window))
        # also treat final fields assigned only via ctor as candidate; injection flag false
        out.append((type_name, field, _line_at(source, m.start()), injected))
    return out


def parse_java_imports(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for m in _IMPORT_RE.finditer(source):
        target = m.group(2)
        line = _line_at(source, m.start())
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
        line = _line_at(source, m.start())
        edges.append(
            {
                "source": f"{rel_path}:{m.group(1)}",
                "target": m.group(2),
                "relation_type": "inherits",
                "status": "observed",
                "start_line": line,
            }
        )
    for m in _IMPLEMENTS_RE.finditer(source):
        cls = m.group(1)
        line = _line_at(source, m.start())
        for raw in m.group(2).split(","):
            iface = _simple_type(raw)
            if not iface or iface in _KEYWORDS:
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{cls}",
                    "target": iface,
                    "relation_type": "implements",
                    "status": "observed",
                    "start_line": line,
                }
            )
    return edges


def parse_java_injections(path: Path, *, rel_path: str) -> list[dict]:
    """Spring-style DI edges: @Autowired/@Inject fields and constructor params."""
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    for type_name, field, line, injected in _fields(source):
        if not injected:
            continue
        owner = _enclosing_type(source, source.find(f"{type_name} {field}"))
        # fallback: re-find position
        if owner is None:
            # approximate via field line scan
            pos = 0
            for m in _FIELD_RE.finditer(source):
                if m.group(2) == field and _simple_type(m.group(1)) == type_name:
                    pos = m.start()
                    break
            owner = _enclosing_type(source, pos) or Path(rel_path).stem
        edges.append(
            {
                "source": f"{rel_path}:{owner}",
                "target": type_name,
                "relation_type": "injects",
                "status": "derived",
                "start_line": line,
            }
        )

    for m in _CTOR_RE.finditer(source):
        cls = m.group(1)
        params = m.group(2).strip()
        line = _line_at(source, m.start())
        if not params:
            continue
        for part in params.split(","):
            part = part.strip()
            if not part:
                continue
            # Type name
            tokens = part.replace("...", " ").split()
            # drop annotations
            tokens = [t for t in tokens if not t.startswith("@")]
            if len(tokens) < 2:
                continue
            type_name = _simple_type(tokens[-2])
            if type_name in _KEYWORDS or type_name[0].islower():
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{cls}",
                    "target": type_name,
                    "relation_type": "injects",
                    "status": "derived",
                    "start_line": line,
                }
            )
    return edges


def _param_types(params: str) -> list[str]:
    out: list[str] = []
    if not params.strip():
        return out
    for part in params.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = [t for t in part.replace("...", " ").split() if not t.startswith("@")]
        if len(tokens) < 2:
            continue
        type_name = _simple_type(tokens[-2])
        if type_name and type_name[0].isupper() and type_name not in _USES_TYPE_SKIP:
            out.append(type_name)
    return out


def parse_java_type_uses(path: Path, *, rel_path: str) -> list[dict]:
    """Method return / parameter types as uses_type (class → type)."""
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    edges: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for m in _METHOD_SIG_RE.finditer(source):
        ret = _simple_type(m.group(1))
        method = m.group(2)
        params = m.group(3)
        if method in _KEYWORDS:
            continue
        owner = _enclosing_type(source, m.start()) or Path(rel_path).stem
        # Skip constructors (return token is the class name in our regex rarely;
        # ctor matched separately by _CTOR_RE — here method==owner is ctor-like).
        if method == owner:
            continue
        line = _line_at(source, m.start())
        types = []
        if ret and ret[0].isupper() and ret not in _USES_TYPE_SKIP:
            types.append(ret)
        types.extend(_param_types(params))
        for type_name in types:
            key = (owner, type_name, line)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "source": f"{rel_path}:{owner}",
                    "target": type_name,
                    "relation_type": "uses_type",
                    "status": "derived",
                    "start_line": line,
                }
            )
    return edges


def parse_java_calls(path: Path, *, rel_path: str) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    field_types = {name: typ for typ, name, _line, _inj in _fields(source)}
    edges: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for m in _CALL_RE.finditer(source):
        target = m.group(1)
        leaf = target.split(".")[-1]
        if leaf in _KEYWORDS or target in _KEYWORDS:
            continue
        line = _line_at(source, m.start())
        owner_type = _enclosing_type(source, m.start()) or "module"
        owner_method = _enclosing_method(source, m.start()) or "module"
        source_sym = f"{rel_path}:{owner_type}.{owner_method}"

        resolved = target
        if "." in target:
            recv, meth = target.rsplit(".", 1)
            if recv in field_types:
                resolved = f"{field_types[recv]}.{meth}"
            elif recv == "this" and owner_type:
                resolved = f"{owner_type}.{meth}"
        # F3: drop tautological self-calls (bare method/ctor name matching enclosure).
        resolved_leaf = resolved.split(".")[-1]
        if resolved_leaf == owner_method:
            continue
        if resolved in {owner_type, f"{owner_type}.{owner_type}"} or resolved_leaf == owner_type:
            continue
        key = (source_sym, resolved, line)
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                "source": source_sym,
                "target": resolved,
                "relation_type": "calls",
                "status": "derived",
                "start_line": line,
            }
        )
    return edges


def parse_java_relations(path: Path, *, rel_path: str) -> list[dict]:
    return (
        parse_java_imports(path, rel_path=rel_path)
        + parse_java_injections(path, rel_path=rel_path)
        + parse_java_type_uses(path, rel_path=rel_path)
        + parse_java_calls(path, rel_path=rel_path)
    )
