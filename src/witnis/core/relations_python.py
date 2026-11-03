from __future__ import annotations

import ast
from pathlib import Path


def parse_python_imports(path: Path, *, rel_path: str) -> list[dict]:
    """Extract import edges as observed relations (module-level)."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    edges: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(
                    {
                        "source": rel_path,
                        "target": alias.name,
                        "relation_type": "imports",
                        "status": "observed",
                        "start_line": node.lineno,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                target = f"{module}.{alias.name}" if module else alias.name
                edges.append(
                    {
                        "source": rel_path,
                        "target": target,
                        "relation_type": "imports_from",
                        "status": "observed",
                        "start_line": node.lineno,
                    }
                )
    return edges


def _base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
        return None
    return None


def parse_python_inheritance(path: Path, *, rel_path: str) -> list[dict]:
    """Extract class inheritance edges (subclass -> base)."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    edges: list[dict] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not node.bases:
            continue
        for base in node.bases:
            name = _base_name(base)
            if not name:
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{node.name}",
                    "target": name,
                    "relation_type": "inherits",
                    "status": "observed",
                    "start_line": node.lineno,
                }
            )
    return edges


def parse_python_decorators(path: Path, *, rel_path: str) -> list[dict]:
    """Extract decorator edges for functions/methods/classes."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    edges: list[dict] = []

    def _emit(owner: str, decorators: list[ast.AST], lineno: int) -> None:
        for dec in decorators:
            name = _base_name(dec)
            if name is None and isinstance(dec, ast.Call):
                name = _base_name(dec.func)
            if not name:
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{owner}",
                    "target": name,
                    "relation_type": "decorated_by",
                    "status": "observed",
                    "start_line": lineno,
                }
            )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            _emit(node.name, list(node.decorator_list), node.lineno)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _emit(
                        f"{node.name}.{child.name}",
                        list(child.decorator_list),
                        child.lineno,
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _emit(node.name, list(node.decorator_list), node.lineno)
    return edges


def parse_python_overrides(path: Path, *, rel_path: str) -> list[dict]:
    """Emit overrides edges for methods that share a name with an inherited base."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    # Map local class -> method names defined on that class
    class_methods: dict[str, set[str]] = {}
    class_bases: dict[str, list[str]] = {}
    method_lines: dict[tuple[str, str], int] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods: set[str] = set()
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.add(child.name)
                method_lines[(node.name, child.name)] = child.lineno
        class_methods[node.name] = methods
        bases = []
        for base in node.bases:
            name = _base_name(base)
            if name:
                bases.append(name.split(".")[-1])
        class_bases[node.name] = bases

    edges: list[dict] = []
    for cls, methods in class_methods.items():
        for base in class_bases.get(cls, []):
            # Same-file base methods, or assume base.method exists when inheriting.
            base_methods = class_methods.get(base)
            for method in methods:
                if base_methods is not None and method not in base_methods:
                    continue
                if base_methods is None and method.startswith("__"):
                    continue
                edges.append(
                    {
                        "source": f"{rel_path}:{cls}.{method}",
                        "target": f"{base}.{method}",
                        "relation_type": "overrides",
                        "status": "derived" if base_methods is None else "observed",
                        "start_line": method_lines.get((cls, method)),
                    }
                )
    return edges
