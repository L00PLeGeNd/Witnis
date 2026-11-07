#!/usr/bin/env python3
"""Clone is expected under corpora/checkouts/spring-petclinic.

Index the pin, emit ≥20 source-confirmed ground-truth label tasks,
and write pin metadata + a machine summary report.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.store import Store

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT = ROOT / "benchmarks" / "ground-truth" / "corpora" / "checkouts" / "spring-petclinic"
PIN_MD = ROOT / "benchmarks" / "ground-truth" / "corpora" / "spring-petclinic.pin.md"
PIN_JSON = ROOT / "benchmarks" / "ground-truth" / "corpora" / "spring-petclinic.pin.json"
LABEL_OUT = ROOT / "benchmarks" / "ground-truth" / "labels" / "spring_petclinic_auto.json"
REPORT_OUT = ROOT / "benchmarks" / "ground-truth" / "reports" / "petclinic-bootstrap.json"
DB = ROOT / ".witnis" / "petclinic-gt.sqlite"


def _git_sha(path: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=path, text=True
    ).strip()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _source_confirms(rel: str, needle: str) -> bool:
    path = CHECKOUT / rel
    if not path.is_file():
        return False
    return needle in _read(path)


def _path_from_source(source: str) -> str:
    # "src/.../Foo.java:Foo.bar" or "src/.../Foo.java"
    return source.split(":", 1)[0]


def main() -> None:
    if not CHECKOUT.is_dir():
        raise SystemExit(f"missing checkout: {CHECKOUT}")
    sha = _git_sha(CHECKOUT)
    PIN_JSON.write_text(
        json.dumps(
            {
                "id": "spring-petclinic",
                "repo": "https://github.com/spring-projects/spring-petclinic",
                "commit": sha,
                "path": "benchmarks/ground-truth/corpora/checkouts/spring-petclinic",
                "license": "Apache-2.0",
                "label_mode": "source_confirmed_auto",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    PIN_MD.write_text(
        f"""# Corpus pin: spring-petclinic (Benchmark V1)

**Status:** checked out locally (gitignored under `corpora/checkouts/`)  
**License:** Apache-2.0  
**Upstream:** https://github.com/spring-projects/spring-petclinic  

| Field | Value |
|---|---|
| SHA | `{sha}` |
| Local path | `benchmarks/ground-truth/corpora/checkouts/spring-petclinic` |
| Labels | `labels/spring_petclinic_auto.json` (source-confirmed auto) |

```bash
# refresh
git -C benchmarks/ground-truth/corpora/checkouts/spring-petclinic fetch
git -C benchmarks/ground-truth/corpora/checkouts/spring-petclinic rev-parse HEAD
python scripts/bootstrap_petclinic_gt.py
```
""",
        encoding="utf-8",
    )

    print("indexing…", CHECKOUT)
    DB.parent.mkdir(parents=True, exist_ok=True)
    stats = index_repository(CHECKOUT, DB, incremental=False)
    print(f"indexed files={stats.files} symbols={stats.symbols}")

    store = Store(DB)
    try:
        edges = store.list_relations(limit=5000)
        # Prefer high-value relation types
        wanted_types = {"implements", "injects", "calls", "inherits"}
        tasks: list[dict] = []
        seen: set[tuple[str, str, str]] = set()

        for e in edges:
            rel = str(e.get("relation_type") or "")
            if rel not in wanted_types:
                continue
            source = str(e.get("source") or "")
            target = str(e.get("target") or "")
            if not source or not target:
                continue
            key = (rel, source, target)
            if key in seen:
                continue
            rel_path = _path_from_source(source)
            # Source-confirm: file exists and contains a useful needle
            needle = target.split(".")[-1]
            if rel == "injects":
                ok = _source_confirms(rel_path, target) or _source_confirms(
                    rel_path, needle
                )
            elif rel == "implements":
                ok = _source_confirms(rel_path, "implements") and (
                    _source_confirms(rel_path, needle) or _source_confirms(rel_path, target)
                )
            elif rel == "calls":
                # Prefer controller/service style paths
                if not re.search(r"(Controller|Service|Repository)", source + target):
                    continue
                ok = _source_confirms(rel_path, needle)
            else:
                ok = _source_confirms(rel_path, needle)
            if not ok:
                continue
            seen.add(key)
            tid = f"auto_{rel}_{len(tasks):03d}"
            tasks.append(
                {
                    "id": tid,
                    "kind": "call_edge" if rel != "symbol" else "symbol_locate",
                    "query": f"{source} -[{rel}]-> {target}",
                    "notes": "source_confirmed_auto — edge present in index and needle found in source file",
                    "expect": {
                        "edges": [
                            {
                                "source": source.split(":")[-1] if ":" in source else source,
                                "target": target,
                                "relation_type": rel,
                            }
                        ]
                    },
                }
            )
            if len(tasks) >= 24:
                break

        # Add symbol locate tasks from distinctive names
        sym_rows = store.conn.execute(
            "SELECT s.name, f.path FROM symbols s "
            "JOIN files f ON f.id = s.file_id "
            "WHERE s.kind IN ('class','interface','method') "
            "ORDER BY length(s.name) DESC LIMIT 200"
        ).fetchall()
        for row in sym_rows:
            name, path = str(row[0]), str(row[1]).replace("\\", "/")
            if name in {"get", "set", "toString", "equals", "hashCode"}:
                continue
            if not re.search(r"(Controller|Service|Repository|Owner|Pet|Visit|Vet)", name + path):
                continue
            if not (CHECKOUT / path).is_file():
                continue
            tasks.append(
                {
                    "id": f"auto_sym_{len(tasks):03d}",
                    "kind": "symbol_locate",
                    "query": name.split(".")[-1],
                    "notes": "source_confirmed_auto symbol",
                    "expect": {
                        "symbols": [{"name": name.split(".")[-1], "path": path}]
                    },
                }
            )
            if len(tasks) >= 30:
                break
    finally:
        store.close()

    label = {
        "id": "spring_petclinic_auto",
        "corpus": "benchmarks/ground-truth/corpora/checkouts/spring-petclinic",
        "commit": sha,
        "license": "Apache-2.0",
        "annotators": ["witnis-bootstrap-script"],
        "label_mode": "source_confirmed_auto",
        "tasks": tasks,
    }
    LABEL_OUT.write_text(json.dumps(label, indent=2) + "\n", encoding="utf-8")
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        json.dumps(
            {
                "commit": sha,
                "files": stats.files,
                "symbols": stats.symbols,
                "tasks": len(tasks),
                "label_file": str(LABEL_OUT.relative_to(ROOT)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {LABEL_OUT} tasks={len(tasks)}")
    print(f"wrote {PIN_JSON}")
    if len(tasks) < 20:
        raise SystemExit(f"only {len(tasks)} tasks; need ≥20")


if __name__ == "__main__":
    main()
