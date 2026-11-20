from __future__ import annotations

import ast
from pathlib import Path

from witnis.core.models import Symbol


def parse_python_source(source: str, *, rel_path: str, filename: str = "<blob>") -> list[Symbol]:
    # PowerShell/editors may write UTF-8 BOM; strip so ast.parse does not fail.
    if source.startswith("\ufeff"):
        source = source.lstrip("\ufeff")
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    symbols: list[Symbol] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="class",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
                )
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        Symbol(
                            name=f"{node.name}.{child.name}",
                            kind="method",
                            file_path=rel_path,
                            start_line=child.lineno,
                            end_line=getattr(child, "end_lineno", child.lineno)
                            or child.lineno,
                        )
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="function",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
                )
            )
    return symbols


def parse_python_file(path: Path, *, rel_path: str) -> list[Symbol]:
    source = path.read_text(encoding="utf-8-sig")
    return parse_python_source(source, rel_path=rel_path, filename=str(path))
