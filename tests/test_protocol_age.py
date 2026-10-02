# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""get_age_of_money through the MCP protocol: read-only, one YNAB request."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server

from .mcp_helpers import call, tool_schema

_MONTHS = [
    {"month": f"2026-{month:02d}-01", "age_of_money": days, "deleted": False}
    for month, days in [(5, None), (6, 20), (7, 24), (8, 29), (9, 33), (10, 33)]
]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[AsyncMock]:
    months = AsyncMock(return_value=_MONTHS)
    with (
        patch("avenir_mcp.client.get_months", months),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
    ):
        yield months


def test_age_of_money_is_read_only() -> None:
    """Declared read-only and idempotent: a client may call it without asking."""

    async def annotations() -> Any:
        async with Client(server.mcp) as mcp_client:
            listed = await mcp_client.list_tools()
            return next(tool for tool in listed if tool.name == "get_age_of_money").annotations

    found = asyncio.run(annotations())
    assert found.read_only_hint is True
    assert found.idempotent_hint is True
    assert found.open_world_hint is True


def test_the_months_up_to_today_in_one_request(ynab: AsyncMock) -> None:
    """May to September; October, budgeted ahead, is left out."""
    answer = call("get_age_of_money", {"plan_id": "b1"}).structured_content
    assert [(m["month"], m["days"]) for m in answer["months"]] == [
        ("2026-05", None),
        ("2026-06", 20),
        ("2026-07", 24),
        ("2026-08", 29),
        ("2026-09", 33),
    ]
    assert (answer["days"], answer["as_of"], answer["change"], answer["trend"]) == (
        33,
        "2026-09",
        13,
        "up",
    )
    ynab.assert_awaited_once_with("b1")


def test_fewer_months_on_request(ynab: AsyncMock) -> None:
    """Two months: August and September."""
    answer = call("get_age_of_money", {"plan_id": "b1", "months_count": 2}).structured_content
    assert [m["month"] for m in answer["months"]] == ["2026-08", "2026-09"]
    assert ynab.await_count == 1


@pytest.mark.parametrize("months", [0, 25])
def test_months_out_of_range_are_refused_before_any_request(ynab: AsyncMock, months: int) -> None:
    """Refused before YNAB is asked anything."""
    answer = call("get_age_of_money", {"plan_id": "b1", "months_count": months})
    assert answer.is_error
    assert ynab.await_count == 0


def test_the_schema_states_the_range_of_months() -> None:
    """The agent sees 1 to 24 before calling, 12 by default."""
    prop = tool_schema("get_age_of_money")["properties"]["months_count"]
    assert (prop["minimum"], prop["maximum"], prop["default"]) == (1, 24, 12)
