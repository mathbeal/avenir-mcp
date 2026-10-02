# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""get_savings_rate through the MCP protocol: read-only, three YNAB requests."""

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

_ACCOUNTS = [
    {"id": "a-chk", "name": "Checking", "type": "checking", "on_budget": True, "closed": False}
    | {"balance": 2_400.0},
    {"id": "a-etf", "name": "Brokerage", "type": "otherAsset", "on_budget": False}
    | {"closed": False, "balance": 9_000.0},
]
_CATEGORIES = [
    {"id": "cat-inflow", "name": "Inflow: Ready to Assign"}
    | {"category_group_name": "Internal Master Category"},
    {"id": "cat-rent", "name": "Rent", "category_group_name": "Bills"},
]


def _tx(month: int, amount: int, category: str | None, transfer: str | None = None) -> Any:
    return {
        "account_id": "a-chk",
        "date": f"2026-{month:02d}-03",
        "amount": amount,
        "payee_name": "Payee",
        "category_id": category,
        "transfer_account_id": transfer,
        "deleted": False,
    }


_HISTORY = [
    tx
    for month in range(3, 9)
    for tx in (
        _tx(month, 2_000_000, "cat-inflow"),
        _tx(month, -1_200_000, "cat-rent"),
        _tx(month, -300_000, None, "a-etf"),
    )
]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[dict[str, AsyncMock]]:
    mocks = {
        "get_accounts": AsyncMock(return_value=_ACCOUNTS),
        "get_categories": AsyncMock(return_value=_CATEGORIES),
        "get_transactions": AsyncMock(return_value=_HISTORY),
    }
    with (
        patch("avenir_mcp.client.get_accounts", mocks["get_accounts"]),
        patch("avenir_mcp.client.get_categories", mocks["get_categories"]),
        patch("avenir_mcp.client.get_transactions", mocks["get_transactions"]),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
    ):
        yield mocks


def test_savings_rate_is_read_only() -> None:
    """Declared read-only and idempotent: a client may call it without asking."""

    async def annotations() -> Any:
        async with Client(server.mcp) as mcp_client:
            listed = await mcp_client.list_tools()
            return next(tool for tool in listed if tool.name == "get_savings_rate").annotations

    found = asyncio.run(annotations())
    assert found.read_only_hint is True
    assert found.idempotent_hint is True
    assert found.open_world_hint is True


def test_six_months_in_three_requests(ynab: dict[str, AsyncMock]) -> None:
    """2,000 in, 1,200 spent, 300 to the brokerage: 800 kept a month, 40.0 %."""
    answer = call("get_savings_rate", {"plan_id": "b1"}).structured_content
    assert [m["month"] for m in answer["months"]] == [
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
    ]
    assert answer["months"][0] == {
        "month": "2026-03",
        "income": 2_000.0,
        "spending": -1_200.0,
        "saved": 800.0,
        "rate": 40.0,
    }
    assert (answer["income"], answer["saved"], answer["rate"]) == (12_000.0, 4_800.0, 40.0)
    assert answer["moved_to_tracking"] == 1_800.0
    assert all(mock.await_count == 1 for mock in ynab.values())


def test_fewer_months_on_request(ynab: dict[str, AsyncMock]) -> None:
    """Two months: July and August."""
    answer = call("get_savings_rate", {"plan_id": "b1", "months_count": 2}).structured_content
    assert [m["month"] for m in answer["months"]] == ["2026-07", "2026-08"]
    ynab["get_transactions"].assert_awaited_once_with("b1")


@pytest.mark.parametrize("months", [0, 25])
def test_months_out_of_range_are_refused_before_any_request(
    ynab: dict[str, AsyncMock], months: int
) -> None:
    """Refused before YNAB is asked anything."""
    answer = call("get_savings_rate", {"plan_id": "b1", "months_count": months})
    assert answer.is_error
    assert all(mock.await_count == 0 for mock in ynab.values())


def test_the_schema_states_the_range_of_months() -> None:
    """The agent sees 1 to 24 before calling."""
    prop = tool_schema("get_savings_rate")["properties"]["months_count"]
    assert (prop["minimum"], prop["maximum"], prop["default"]) == (1, 24, 6)
