"""Every tool says what it does, and writes are off unless enabled."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp import Client

from avenir_mcp import app, server


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


def test_configuring_again_and_again_adds_nothing_to_the_server() -> None:
    """Each call switches the same gate: a thousand calls leave the server as one call does.

    configure used to add a visibility filter per call; the test suite calls it twice per
    test, and past some 570 tests FastMCP ran out of recursion depth looking a tool up.
    """
    before = len(server.mcp.transforms)
    for _ in range(500):
        server.configure(enable_writes=False)
        server.configure(enable_writes=True)
    assert len(server.mcp.transforms) == before
    assert "apply_categories" in {t.name for t in _tools()}
    server.configure(enable_writes=False)
    assert "apply_categories" not in {t.name for t in _tools()}


def test_read_only_descriptions_name_no_hidden_tool() -> None:
    """Read-only, no visible tool points the agent to a tool it cannot see."""
    server.configure(enable_writes=True)
    every = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    server.configure(enable_writes=False)
    visible = asyncio.run(server.mcp.list_tools())
    hidden = every - {tool.name for tool in visible}
    assert hidden
    for tool in visible:
        named = {name for name in hidden if re.search(rf"\b{name}\b", tool.description or "")}
        assert not named, f"{tool.name} names {sorted(named)}"


def test_with_writes_the_descriptions_name_the_write_tools() -> None:
    """With writes on, suggest_categories still routes to apply_categories."""
    server.configure(enable_writes=True)
    tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
    assert "apply_categories" in (tools["suggest_categories"].description or "")
    assert "create_category" in (tools["list_category_groups"].description or "")


def test_every_read_only_wording_matches_its_description() -> None:
    """A declared sentence that no longer appears would silently stop replacing anything."""
    server.configure(enable_writes=True)
    tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
    wordings = app._READ_ONLY_WORDING  # pylint: disable=protected-access
    assert wordings
    for name, (sentence, _replacement) in wordings.items():
        assert sentence in (tools[name].description or ""), name
