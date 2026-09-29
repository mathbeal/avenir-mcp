"""Numeric arguments are bounded in the schema, so an agent sees the range before calling."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server
from tests.mcp_helpers import call


def _input_schema(name: str) -> dict[str, Any]:
    async def run() -> dict[str, Any]:
        async with Client(server.mcp) as mcp_client:
            tool = next(t for t in await mcp_client.list_tools() if t.name == name)
            schema: dict[str, Any] = tool.input_schema
            return schema

    return asyncio.run(run())


@pytest.mark.parametrize(
    ("tool", "argument", "minimum", "maximum"),
    [
        ("get_spending_trends", "months_count", 1, 24),
        ("suggest_categories", "limit", 1, 200),
    ],
)
def test_the_schema_states_the_range_of_a_count(
    tool: str, argument: str, minimum: int, maximum: int
) -> None:
    """The range is in the input schema, where the agent reads it before the call."""
    prop = _input_schema(tool)["properties"][argument]
    assert (prop["minimum"], prop["maximum"]) == (minimum, maximum)


@pytest.mark.parametrize("months_count", [0, -2, 25])
def test_a_trend_outside_the_range_is_refused_before_any_request(months_count: int) -> None:
    """Zero once fetched every month of the plan: a slice [-0:] is the whole list."""
    with patch("avenir_mcp.client.get_months", new=AsyncMock(return_value=[])) as months:
        result = call("get_spending_trends", {"plan_id": "b1", "months_count": months_count})
    assert result.is_error
    months.assert_not_awaited()


@pytest.mark.parametrize("limit", [0, -1, 201])
def test_a_page_size_outside_the_range_is_refused_before_any_request(limit: int) -> None:
    """A page of zero returned the same cursor again, and an agent paging on it never ended."""
    with patch("avenir_mcp.client.get_transactions", new=AsyncMock(return_value=[])) as reads:
        result = call("suggest_categories", {"plan_id": "b1", "limit": limit})
    assert result.is_error
    reads.assert_not_awaited()
