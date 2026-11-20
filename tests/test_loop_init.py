from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from witnis.cli import app
from witnis.core.loop_init import init_trusted_loop

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"
runner = CliRunner()


def test_init_trusted_loop_writes_harnis_wrap(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    # Copy a tiny source tree so index has something to chew
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "a.py").write_text("def login():\n    return 1\n", encoding="utf-8")

    payload = init_trusted_loop(root, with_harnis=True, index=True)
    assert payload["status"] == "success"
    result = payload["result"]
    assert result["with_harnis"] is True
    assert result["indexed"] is True

    mcp_path = Path(result["mcp_config"])
    assert mcp_path.is_file()
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["witnis"]
    assert server["command"] == "npx"
    assert "harnis" in server["args"]
    assert "uvx" in server["args"]
    assert "git+https://github.com/L00PLeGeNd/Witnis.git" in server["args"]
    assert server["args"][-2:] == ["witnis", "mcp"]
    assert Path(server["env"]["WITNIS_DB"]).name == "index.sqlite"

    policy = Path(result["policy"])
    assert policy.is_file()
    loop = (root / ".witnis" / "LOOP.txt").read_text(encoding="utf-8")
    assert "automation_verified" in loop
    assert "witnis-dev" in loop
    assert "pr-gate" in loop


def test_init_trusted_loop_bare_skips_harnis(tmp_path: Path) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    (root / "x.py").write_text("x = 1\n", encoding="utf-8")
    payload = init_trusted_loop(root, with_harnis=False, index=False)
    assert payload["status"] == "success"
    assert payload["result"]["with_harnis"] is False
    assert payload["result"]["policy"] is None
    mcp = json.loads(Path(payload["result"]["mcp_config"]).read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["witnis"]
    assert server["command"] == "uvx"
    assert server["args"] == [
        "--from",
        "git+https://github.com/L00PLeGeNd/Witnis.git",
        "witnis",
        "mcp",
    ]
    assert not (root / ".harnis").exists()


def test_loop_init_cli(tmp_path: Path) -> None:
    root = tmp_path / "cli_repo"
    root.mkdir()
    (root / "m.py").write_text("def foo():\n    pass\n", encoding="utf-8")
    result = runner.invoke(
        app,
        ["loop-init", str(root), "--no-index", "--deny-verify"],
    )
    assert result.exit_code == 0, result.output
    body = json.loads(result.output)
    assert body["status"] == "success"
    assert body["result"]["with_harnis"] is True
    policy = json.loads(Path(body["result"]["policy"]).read_text(encoding="utf-8"))
    assert "verify" in policy["deny_tools"]
    assert "run_verification" in policy["deny_tools"]
