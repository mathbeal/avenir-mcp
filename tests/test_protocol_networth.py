# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""get_net_worth_trend through the MCP protocol: read-only, two YNAB requests."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server

from .mcp_helpers import call

_ACCOUNTS = [
    {"id": "a-chk", "name": "Checking", "type": "checking", "on_budget": True, "closed": False}
    | {"balance": 2_000.0},
    {"id": "a-car", "name": "Car loan", "type": "autoLoan", "on_budget": False, "closed": False}
    | {"balance": -4_000.0},
]
_PAYMENT = [
    {"account_id": "a-chk", "date": "2026-09-10", "amount": -400_000, "deleted": False},
    {"account_id": "a-car", "date": "2026-09-10", "amount": 400_000, "deleted": False},
    {"account_id": "a-chk", "date": "2026-09-24", "amount": 1_000_000, "deleted": False},
]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[dict[str, AsyncMock]]:
    mocks = {
        "get_accounts": AsyncMock(return_value=_ACCOUNTS),
        "get_transactions": AsyncMock(return_value=_PAYMENT),
    }
    with (
        patch("avenir_mcp.client.get_accounts", mocks["get_accounts"]),
        patch("avenir_mcp.client.get_transactions", mocks["get_transactions"]),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
    ):
        yield mocks


def test_net_worth_is_read_only() -> None:
    """Declared read-only and idempotent: a client may call it without asking."""

    async def annotations() -> Any:
        async with Client(server.mcp) as mcp_client:
            tools = {tool.name: tool for tool in await mcp_client.list_tools()}
            return tools["get_net_worth_trend"].annotations

    found = asyncio.run(annotations())
    assert (found.read_only_hint, found.idempotent_hint, found.open_world_hint) == (
        True,
        True,
        True,
    )


def test_net_worth_month_by_month_in_two_requests(ynab: dict[str, AsyncMock]) -> None:
    """A car loan paid 400 in September, a salary of 1,000: net worth up by 1,000."""
    answer = call("get_net_worth_trend", {"plan_id": "b1", "months_count": 2}).structured_content
    assert answer["months"] == [
        {"month": "2026-08-01", "assets": 1_400.0, "debts": -4_400.0, "net_worth": -3_000.0},
        {"month": "2026-09-01", "assets": 2_000.0, "debts": -4_000.0, "net_worth": -2_000.0},
    ]
    assert (answer["first_net_worth"], answer["last_net_worth"], answer["change"]) == (
        -3_000.0,
        -2_000.0,
        1_000.0,
    )
    assert answer["accounts"] == ["Checking", "Car loan"]
    assert all(mock.await_count == 1 for mock in ynab.values())


def test_twelve_months_by_default(ynab: dict[str, AsyncMock]) -> None:
    """Without months_count, a year: October to September."""
    answer = call("get_net_worth_trend", {"plan_id": "b1"}).structured_content
    assert len(answer["months"]) == 12
    assert answer["months"][0]["month"] == "2025-10-01"
    assert ynab["get_accounts"].await_count == 1


@pytest.mark.parametrize("months_count", [0, 25])
def test_months_count_outside_one_to_twenty_four_is_refused(
    ynab: dict[str, AsyncMock], months_count: int
) -> None:
    """Refused before YNAB is asked anything."""
    answer = call("get_net_worth_trend", {"plan_id": "b1", "months_count": months_count})
    assert answer.is_error
    assert ynab["get_accounts"].await_count == 0
