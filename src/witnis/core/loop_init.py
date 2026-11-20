"""Bootstrap Trusted Agent Loop configs (Witnis + optional Harnis seatbelt)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.index import index_repository


def _db_path_for(root: Path) -> Path:
    return (root / ".witnis" / "index.sqlite").resolve()


def _uvx_witnis_mcp() -> tuple[str, list[str]]:
    return "uvx", ["witnis", "mcp"]


def build_mcp_witnis_only(*, db: Path) -> dict[str, Any]:
    command, args = _uvx_witnis_mcp()
    return {
        "mcpServers": {
            "witnis": {
                "command": command,
                "args": args,
                "env": {"WITNIS_DB": str(db)},
            }
        }
    }


def build_mcp_witnis_behind_harnis(
    *,
    db: Path,
    policy: Path,
    use_npx: bool = True,
) -> dict[str, Any]:
    policy_s = str(policy.resolve())
    uvx_cmd, uvx_args = _uvx_witnis_mcp()
    if use_npx:
        args = [
            "-y",
            "harnis",
            "mcp",
            "--preset",
            "coding-agent",
            "--policy",
            policy_s,
            "--",
            uvx_cmd,
            *uvx_args,
        ]
        command = "npx"
    else:
        args = [
            "-m",
            "harnis",
            "mcp",
            "--preset",
            "coding-agent",
            "--policy",
            policy_s,
            "--",
            "python",
            "-m",
            "witnis",
            "mcp",
        ]
        command = "python"
    return {
        "mcpServers": {
            "witnis": {
                "command": command,
                "args": args,
                "env": {"WITNIS_DB": str(db)},
            }
        }
    }


def default_harnis_policy(*, deny_verify: bool = False) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "deny_tools": [],
        "empty_edit_limit": 5,
        "max_tool_calls": 300,
        "max_unique_paths": 80,
    }
    if deny_verify:
        policy["deny_tools"] = ["verify", "run_verification"]
    return policy


def init_trusted_loop(
    root: Path,
    *,
    with_harnis: bool = True,
    deny_verify: bool = False,
    use_npx: bool = True,
    index: bool = True,
) -> dict[str, Any]:
    """Write loop configs under the repo; optionally index."""
    root = root.resolve()
    witnis_dir = root / ".witnis"
    harnis_dir = root / ".harnis"
    witnis_dir.mkdir(parents=True, exist_ok=True)

    db = _db_path_for(root)
    written: list[str] = []
    limitations: list[str] = [
        "Copy or merge mcp.loop.json into your client MCP config (Claude Code / Cline / Cursor).",
        "Seatbelt is stdio MCP only — not an OS/container sandbox.",
        "Verify stays blocked until WITNIS_ALLOW_VERIFY=1 and explicit execute.",
    ]

    policy_path: Path | None = None
    if with_harnis:
        harnis_dir.mkdir(parents=True, exist_ok=True)
        policy_path = harnis_dir / "policy.json"
        if not policy_path.exists():
            policy_path.write_text(
                json.dumps(
                    default_harnis_policy(deny_verify=deny_verify),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            written.append(str(policy_path.relative_to(root)))
        else:
            limitations.append(f"Left existing {policy_path.as_posix()} unchanged")
        mcp = build_mcp_witnis_behind_harnis(
            db=db, policy=policy_path, use_npx=use_npx
        )
        limitations.append("Seatbelt via npx -y harnis (no extra install).")
    else:
        mcp = build_mcp_witnis_only(db=db)
        limitations.append("Started without Harnis wrap (--no-harnis).")

    mcp_path = witnis_dir / "mcp.loop.json"
    mcp_path.write_text(
        json.dumps(mcp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    written.append(str(mcp_path.relative_to(root)))

    readme = witnis_dir / "LOOP.txt"
    readme.write_text(
        "\n".join(
            [
                "Witnis (witnis-dev) — coding-agent evidence. Seatbelt included.",
                "",
                "1. Merge .witnis/mcp.loop.json into Cursor / Claude MCP config.",
                "2. witnis look <symbol>",
                "3. One GitHub Action: uses: L00PLeGeNd/Witnis/.github/actions/pr-gate@v1",
                "4. Do not tell anyone tests passed unless verify returned automation_verified.",
                "",
                "Not affiliated with Witnis AB / witnis.se.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    written.append(str(readme.relative_to(root)))

    indexed = False
    if index:
        index_repository(root, db, incremental=True)
        indexed = True
        try:
            written.append(str(db.relative_to(root)))
        except ValueError:
            written.append(str(db))

    return make_envelope(
        status="success",
        repository={"name": root.name, "root_path": str(root)},
        result={
            "root": str(root),
            "with_harnis": with_harnis,
            "deny_verify": deny_verify,
            "mcp_config": str(mcp_path),
            "policy": str(policy_path) if policy_path else None,
            "db": str(db),
            "indexed": indexed,
            "written": written,
            "next": [
                "Merge .witnis/mcp.loop.json into the MCP client",
                "witnis look <symbol>",
                "witnis pr-gate --base origin/main --head HEAD",
            ],
        },
        evidence=[
            {
                "type": "loop_init",
                "status": "observed",
                "with_harnis": with_harnis,
                "files": written,
            }
        ],
        limitations=limitations,
    )
