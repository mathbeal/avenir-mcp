"""Every tool says what it does, and writes are off unless enabled."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp import Client

from avenir_mcp import server


def _tools() -> list[Any]:
    async def run() -> list[Any]:
        async with Client(server.mcp) as mcp_client:
            return list(await mcp_client.list_tools())

    return asyncio.run(run())


def test_every_tool_is_annotated() -> None:
    """No tool leaves the client guessing whether it reads or writes."""
    missing = [
        t.name for t in _tools() if t.annotations is None or t.annotations.read_only_hint is None
    ]
    assert not missing


def test_every_write_tool_says_whether_it_destroys_and_can_be_repeated() -> None:
    """A write tool declares destructiveHint and idempotentHint explicitly."""
    for tool in _tools():
        if tool.annotations.read_only_hint is False:
            assert tool.annotations.destructive_hint is not None, tool.name
            assert tool.annotations.idempotent_hint is not None, tool.name


def test_write_tag_matches_the_annotation() -> None:
    """Exactly the tools that write carry the tag that read-only mode hides."""
    for tool in _tools():
        tags = set((tool.meta or {}).get("fastmcp", {}).get("tags", []))
        assert (server.WRITE_TAG in tags) == (tool.annotations.read_only_hint is False), tool.name


def test_read_only_mode_hides_and_refuses_writes() -> None:
    """With writes off, write tools are neither listed nor callable."""
    server.configure(enable_writes=False)
    names = {t.name for t in _tools()}
    assert "suggest_categories" in names
    assert "apply_categories" not in names
    assert "create_transactions" not in names
    assert "split_transaction" not in names

    async def call() -> Any:
        async with Client(server.mcp) as mcp_client:
            return await mcp_client.call_tool(
                "approve_transactions", {"plan_id": "b1", "tx_ids": []}, raise_on_error=False
            )

    assert asyncio.run(call()).is_error


def test_main_keeps_writes_off_unless_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_WRITE=1 is the only way to expose write tools."""
    for value, expected in ((None, False), ("0", False), ("1", True)):
        if value is None:
            monkeypatch.delenv("AVENIR_MCP_WRITE", raising=False)
        else:
            monkeypatch.setenv("AVENIR_MCP_WRITE", value)
        with patch.object(server, "configure") as configure, patch.object(server.mcp, "run"):
            server.main()
        configure.assert_called_once_with(enable_writes=expected)


def test_writes_can_be_enabled_again() -> None:
    """configure(enable_writes=True) brings write tools back."""
    server.configure(enable_writes=False)
    server.configure(enable_writes=True)
    assert "apply_categories" in {t.name for t in _tools()}
