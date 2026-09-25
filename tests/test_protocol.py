"""Tests through the MCP protocol: what a client actually sees."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

from fastmcp import Client

from avenir_mcp import server

_TXS: list[dict[str, Any]] = [
    {
        "id": f"h{i}",
        "date": "2026-08-01",
        "amount": -5000,
        "payee_name": "CORNER SHOP",
        "memo": None,
        "account_name": "Checking",
        "category_id": "c-food",
        "transfer_account_id": None,
        "deleted": False,
    }
    for i in range(3)
] + [
    {
        "id": "p1",
        "date": "2026-09-02",
        "amount": -7250,
        "payee_name": "CORNER SHOP",
        "memo": None,
        "account_name": "Checking",
        "category_id": None,
        "transfer_account_id": None,
        "deleted": False,
    }
]
_CATS = [{"id": "c-food", "name": "Groceries", "category_group_name": "Everyday"}]


async def _tool(name: str) -> Any:
    async with Client(server.mcp) as mcp_client:
        return next(t for t in await mcp_client.list_tools() if t.name == name)


async def _call(name: str, args: dict[str, Any]) -> Any:
    async with Client(server.mcp) as mcp_client:
        return await mcp_client.call_tool(name, args, raise_on_error=False)


def test_suggest_categories_is_declared_read_only() -> None:
    """Clients may run it without confirmation: it changes nothing."""
    tool = asyncio.run(_tool("suggest_categories"))
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.open_world_hint is True


def test_suggest_categories_publishes_a_precise_output_schema() -> None:
    """The output schema names the fields, so a client can validate the answer."""
    schema = asyncio.run(_tool("suggest_categories")).output_schema
    assert {"pending_count", "suggested_count", "items", "categories", "next_cursor"} <= set(
        schema["properties"]
    )


def test_suggest_categories_returns_structured_content_in_two_requests() -> None:
    """One page of suggestions costs two YNAB requests, whatever the number of items."""
    get_txs = AsyncMock(return_value=_TXS)
    get_cats = AsyncMock(return_value=_CATS)
    with (
        patch("avenir_mcp.client.get_transactions", get_txs),
        patch("avenir_mcp.client.get_categories", get_cats),
    ):
        result = asyncio.run(_call("suggest_categories", {"budget_id": "b1"}))
    assert not result.is_error
    data = result.structured_content
    assert data["pending_count"] == 1
    assert data["items"][0]["amount"] == -7.25
    assert data["items"][0]["suggestion"]["category_name"] == "Groceries"
    get_txs.assert_awaited_once_with("b1")
    get_cats.assert_awaited_once_with("b1")


def test_suggest_categories_reports_a_bad_cursor_as_a_tool_error() -> None:
    """A bad cursor comes back as isError with a message the model can act on."""
    with (
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=[])),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
    ):
        result = asyncio.run(_call("suggest_categories", {"budget_id": "b1", "cursor": "x"}))
    assert result.is_error
    assert "next_cursor" in result.content[0].text
