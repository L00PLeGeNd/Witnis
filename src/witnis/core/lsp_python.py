from __future__ import annotations

from pathlib import Path
from typing import Any


def lsp_available() -> bool:
    try:
        import jedi  # noqa: F401
    except ImportError:
        return False
    return True


def _rel(root: Path, module_path: Any) -> str:
    if not module_path:
        return ""
    try:
        return Path(module_path).resolve().relative_to(root).as_posix()
    except ValueError:
        return str(module_path)


def lsp_definitions(
    root: Path,
    name: str,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    """Resolve definitions via Jedi (optional LSP-class enrichment)."""
    root = root.resolve()
    if not lsp_available():
        return {
            "backend": None,
            "definitions": [],
            "available": False,
            "limitation": "Install optional extra: pip install 'witnis[lsp]' (jedi)",
        }
    import jedi

    leaf = name.split(".")[-1]
    project = jedi.Project(path=str(root))
    definitions: list[dict[str, Any]] = []
    try:
        results = list(project.search(leaf))
    except Exception:
        results = []
    for d in results:
        item = {
            "name": getattr(d, "name", leaf),
            "kind": str(getattr(d, "type", "unknown")),
            "path": _rel(root, getattr(d, "module_path", None)),
            "line": getattr(d, "line", None),
            "column": getattr(d, "column", None),
            "full_name": getattr(d, "full_name", None),
        }
        if item["path"] and item not in definitions:
            definitions.append(item)
        if len(definitions) >= limit:
            break
    return {
        "backend": "jedi",
        "definitions": definitions[:limit],
        "available": True,
        "limitation": None if definitions else "No Jedi definitions found for name",
    }


def lsp_references(
    root: Path,
    name: str,
    *,
    limit: int = 40,
) -> dict[str, Any]:
    """Find references via Jedi, anchored at the first matching definition site."""
    root = root.resolve()
    if not lsp_available():
        return {
            "backend": None,
            "references": [],
            "available": False,
            "limitation": "Install optional extra: pip install 'witnis[lsp]' (jedi)",
        }
    import jedi

    leaf = name.split(".")[-1]
    defs = lsp_definitions(root, leaf, limit=5)
    refs: list[dict[str, Any]] = []
    project = jedi.Project(path=str(root))
    for d in defs.get("definitions") or []:
        path = root / str(d.get("path") or "")
        line = d.get("line")
        col = d.get("column")
        if not path.is_file() or not line:
            continue
        try:
            source = path.read_text(encoding="utf-8")
            script = jedi.Script(source, path=path, project=project)
            column = int(col or 0) + max(len(leaf) - 1, 0)
            found = script.get_references(int(line), column, include_builtins=False)
        except Exception:
            continue
        for r in found:
            item = {
                "name": r.name,
                "path": _rel(root, r.module_path),
                "line": r.line,
                "column": r.column,
            }
            if item["path"] and item not in refs:
                refs.append(item)
            if len(refs) >= limit:
                break
        if len(refs) >= limit:
            break
    return {
        "backend": "jedi",
        "references": refs[:limit],
        "available": True,
        "limitation": None if refs else "No Jedi references found for name",
    }


def index_definitions(store: Any, name: str, *, limit: int = 20) -> dict[str, Any]:
    """Fallback definitions from the Witnis symbol index (always available post-index)."""
    leaf = name.split(".")[-1]
    hits = store.search(name, limit=limit) or []
    if not hits and leaf != name:
        hits = store.search(leaf, limit=limit) or []
    definitions: list[dict[str, Any]] = []
    for h in hits:
        item = {
            "name": h.get("name"),
            "kind": h.get("kind"),
            "path": h.get("file_path"),
            "line": h.get("start_line"),
            "column": 0,
            "full_name": h.get("name"),
        }
        if item["path"] and item not in definitions:
            definitions.append(item)
        if len(definitions) >= limit:
            break
    return {
        "backend": "index",
        "definitions": definitions[:limit],
        "available": True,
        "limitation": None if definitions else "No index symbols matched name",
    }


def index_references(store: Any, name: str, *, limit: int = 40) -> dict[str, Any]:
    """Fallback references from relation edges + same-name symbol sites."""
    leaf = name.split(".")[-1]
    refs: list[dict[str, Any]] = []
    seen: set[tuple] = set()

    for edge in store.list_relations(limit=500) or []:
        target = str(edge.get("target") or "")
        source = str(edge.get("source") or "")
        if leaf not in target and name not in target and leaf not in source and name not in source:
            continue
        # Prefer the source side as a reference site when target matches the symbol.
        site = source if (leaf in target or name in target) else target
        path = site.split(":", 1)[0]
        line = edge.get("start_line")
        item = {"name": leaf, "path": path, "line": line, "column": 0}
        key = (item["path"], item["line"], item["name"])
        if item["path"] and key not in seen:
            seen.add(key)
            refs.append(item)
        if len(refs) >= limit:
            break

    if len(refs) < limit:
        for h in store.search(leaf, limit=limit) or []:
            item = {
                "name": h.get("name"),
                "path": h.get("file_path"),
                "line": h.get("start_line"),
                "column": 0,
            }
            key = (item["path"], item["line"], item["name"])
            if item["path"] and key not in seen:
                seen.add(key)
                refs.append(item)
            if len(refs) >= limit:
                break

    return {
        "backend": "index",
        "references": refs[:limit],
        "available": True,
        "limitation": None if refs else "No index references matched name",
    }
