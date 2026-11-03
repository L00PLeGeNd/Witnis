from __future__ import annotations

import ast
from pathlib import Path


def _qualname(stack: list[str], name: str) -> str:
    return ".".join([*stack, name]) if stack else name


def _attr_chain(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    cur: ast.AST | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return parts
    return None


_BUILTIN_CALLS = {
    "bool",
    "int",
    "str",
    "float",
    "list",
    "dict",
    "set",
    "tuple",
    "len",
    "print",
    "range",
    "type",
    "isinstance",
    "getattr",
    "setattr",
}


def parse_python_calls(path: Path, *, rel_path: str) -> list[dict]:
    """Extract call edges with light import/local/self-attr resolution."""
    source = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    import_map: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                import_map[local] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                import_map[local] = f"{module}.{alias.name}" if module else alias.name

    # classname -> instance attr -> qualified type
    class_attrs: dict[str, dict[str, str]] = {}

    def resolve_constructor(func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            if func.id in import_map:
                return import_map[func.id]
            return func.id
        if isinstance(func, ast.Attribute):
            chain = _attr_chain(func)
            if chain:
                return ".".join(chain)
        return None

    # harvest self.attr = Call(...) from __init__ methods
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        attrs: dict[str, str] = {}
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name != "__init__":
                continue
            for stmt in child.body:
                if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                    continue
                tgt = stmt.targets[0]
                if not (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                ):
                    continue
                if isinstance(stmt.value, ast.Call):
                    resolved = resolve_constructor(stmt.value.func)
                    if resolved:
                        attrs[tgt.attr] = resolved
                elif isinstance(stmt.value, ast.Name) and stmt.value.id in import_map:
                    attrs[tgt.attr] = import_map[stmt.value.id]
        if attrs:
            class_attrs[node.name] = attrs

    edges: list[dict] = []

    def resolve_callee(
        func: ast.AST, local_types: dict[str, str], class_stack: list[str]
    ) -> tuple[str, str]:
        if isinstance(func, ast.Name):
            name = func.id
            if name in import_map:
                return import_map[name], "derived"
            if name in local_types:
                return local_types[name], "derived"
            return name, "derived"
        if isinstance(func, ast.Attribute):
            # obj.method() where obj is Call(...): keep method name + try ctor type
            if isinstance(func.value, ast.Call):
                ctor = resolve_constructor(func.value.func)
                if ctor:
                    return f"{ctor}.{func.attr}", "derived"
                return func.attr, "derived"
            chain = _attr_chain(func)
            if not chain:
                return func.attr, "derived"
            base, *rest = chain
            if base == "self" and class_stack and rest:
                attrs = class_attrs.get(class_stack[0], {})
                field = rest[0]
                if field in attrs:
                    qual = attrs[field]
                    more = rest[1:]
                    if more:
                        return f"{qual}.{'.'.join(more)}", "derived"
                    return qual, "derived"
            if base in local_types:
                qual = local_types[base]
                if rest:
                    return f"{qual}.{'.'.join(rest)}", "derived"
                return qual, "derived"
            if base in import_map:
                qual = import_map[base]
                if rest:
                    return f"{qual}.{'.'.join(rest)}", "derived"
                return qual, "derived"
            return func.attr, "derived"
        return "?", "unverified"

    def walk_fn(fn: ast.AST, class_stack: list[str]) -> None:
        assert isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        caller = _qualname(class_stack, fn.name)
        local_types: dict[str, str] = {}

        for stmt in fn.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                continue
            value = stmt.value
            if isinstance(value, ast.Call):
                resolved, _status = resolve_callee(value.func, local_types, class_stack)
                if resolved != "?":
                    local_types[target.id] = resolved
            elif isinstance(value, ast.Name) and value.id in import_map:
                local_types[target.id] = import_map[value.id]

        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            target, status = resolve_callee(node.func, local_types, class_stack)
            if target == "?" or target in _BUILTIN_CALLS:
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{caller}",
                    "target": target,
                    "relation_type": "calls",
                    "status": status,
                    "start_line": getattr(node, "lineno", fn.lineno),
                }
            )
            short = target.split(".")[-1]
            if short != target:
                edges.append(
                    {
                        "source": f"{rel_path}:{caller}",
                        "target": short,
                        "relation_type": "calls",
                        "status": "derived",
                        "start_line": getattr(node, "lineno", fn.lineno),
                    }
                )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    walk_fn(child, [node.name])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            walk_fn(node, [])
    return edges
