# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""get_runway through the MCP protocol: read-only, two YNAB requests, three with groups."""

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
    {"id": "a-savings", "name": "Savings", "type": "savings", "on_budget": True, "closed": False}
    | {"balance": 600.0},
    {"id": "a-car", "name": "Car loan", "type": "autoLoan", "on_budget": False, "closed": False}
    | {"balance": -4_000.0},
]
_SPENT = [
    {
        "account_id": "a-chk",
        "date": f"2026-{month:02d}-03",
        "amount": amount,
        "category_id": category,
        "transfer_account_id": None,
        "deleted": False,
    }
    for month in range(3, 9)
    for amount, category in ((-700_000, "cat-rent"), (-300_000, "cat-fun"))
]
_GROUPS = [
    {"id": "g-bills", "name": "Bills", "category_ids": ["cat-rent"]},
    {"id": "g-fun", "name": "Fun", "category_ids": ["cat-fun"]},
]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[dict[str, AsyncMock]]:
    mocks = {
        "get_accounts": AsyncMock(return_value=_ACCOUNTS),
        "get_transactions": AsyncMock(return_value=_SPENT),
        "get_category_tree": AsyncMock(return_value=_GROUPS),
    }
    with (
        patch("avenir_mcp.client.get_accounts", mocks["get_accounts"]),
        patch("avenir_mcp.client.get_transactions", mocks["get_transactions"]),
        patch("avenir_mcp.client.get_category_tree", mocks["get_category_tree"]),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
    ):
        yield mocks


def test_runway_is_read_only() -> None:
    """Declared read-only and idempotent: a client may call it without asking."""

    async def annotations() -> Any:
        async with Client(server.mcp) as mcp_client:
            listed = await mcp_client.list_tools()
            return next(tool for tool in listed if tool.name == "get_runway").annotations

    found = asyncio.run(annotations())
    assert found.read_only_hint is True
    assert found.idempotent_hint is True
    assert found.open_world_hint is True


def test_three_months_of_spending_in_two_requests(ynab: dict[str, AsyncMock]) -> None:
    """3,000 available, 1,000 spent a month over the last six months: 3.0 months."""
    answer = call("get_runway", {"plan_id": "b1"}).structured_content
    assert answer["liquid"] == 3_000.0
    assert answer["months"] == ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    assert answer["spending"] == {"monthly_spending": -1_000.0, "runway_months": 3.0}
    assert answer["essential"] is None
    assert [a["name"] for a in answer["accounts"]] == ["Checking", "Savings"]
    assert answer["left_out"] == ["Car loan"]
    assert (ynab["get_accounts"].await_count, ynab["get_transactions"].await_count) == (1, 1)
    ynab["get_category_tree"].assert_not_awaited()


def test_essential_groups_by_name_or_id_in_three_requests(ynab: dict[str, AsyncMock]) -> None:
    """Rent alone, 700 a month: 4.3 months; the savings left out: 3.4."""
    args = {"plan_id": "b1", "essential_groups": ["bills"], "months_count": 3}
    answer = call("get_runway", args).structured_content
    assert answer["months"] == ["2026-06", "2026-07", "2026-08"]
    assert answer["essential"] == {"monthly_spending": -700.0, "runway_months": 4.3}
    assert answer["essential_groups"] == ["Bills"]
    args = {"plan_id": "b1", "essential_groups": ["g-bills"], "include_savings": False}
    answer = call("get_runway", args).structured_content
    assert answer["liquid"] == 2_400.0
    assert answer["essential"]["runway_months"] == 3.4
    assert all(mock.await_count == 2 for mock in ynab.values())


def test_an_unknown_group_is_refused_before_the_accounts_are_read(
    ynab: dict[str, AsyncMock],
) -> None:
    """The error lists the plan's groups, so the agent can ask again."""
    answer = call("get_runway", {"plan_id": "b1", "essential_groups": ["Food"]})
    assert answer.is_error
    assert "'Food'" in answer.content[0].text
    assert "Bills, Fun" in answer.content[0].text
    ynab["get_accounts"].assert_not_awaited()


@pytest.mark.parametrize(
    "args",
    [
        {"months_count": 0},
        {"months_count": 25},
        {"essential_groups": []},
        {"essential_groups": [""]},
    ],
)
def test_arguments_out_of_range_are_refused_before_any_request(
    ynab: dict[str, AsyncMock], args: dict[str, Any]
) -> None:
    """Refused before YNAB is asked anything."""
    answer = call("get_runway", {"plan_id": "b1", **args})
    assert answer.is_error
    assert all(mock.await_count == 0 for mock in ynab.values())


def test_the_schema_states_the_range_of_months() -> None:
    """The agent sees 1 to 24 before calling."""
    prop = tool_schema("get_runway")["properties"]["months_count"]
    assert (prop["minimum"], prop["maximum"], prop["default"]) == (1, 24, 6)
