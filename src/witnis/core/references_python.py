from __future__ import annotations

import ast
from pathlib import Path

_SKIP_NAMES = {
    "True",
    "False",
    "None",
    "self",
    "cls",
}


def parse_python_references(path: Path, *, rel_path: str) -> list[dict]:
    """Extract name-reference edges (Load) inside functions/methods."""
    source = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    edges: list[dict] = []

    def walk_fn(fn: ast.AST, class_stack: list[str]) -> None:
        assert isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        caller = ".".join([*class_stack, fn.name]) if class_stack else fn.name
        local_defs = {a.arg for a in fn.args.args}
        for node in ast.walk(fn):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # skip nested def names themselves as references
                continue
            if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
                continue
            if node.id in _SKIP_NAMES or node.id in local_defs:
                continue
            edges.append(
                {
                    "source": f"{rel_path}:{caller}",
                    "target": node.id,
                    "relation_type": "references",
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
