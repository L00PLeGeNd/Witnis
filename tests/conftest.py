from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _experimental_mcp_catalog(request, monkeypatch):
    """Default tests see the full MCP catalog; public-surface tests opt out."""
    if request.node.get_closest_marker("mcp_public"):
        monkeypatch.delenv("WITNIS_MCP_EXPERIMENTAL", raising=False)
        return
    monkeypatch.setenv("WITNIS_MCP_EXPERIMENTAL", "1")
