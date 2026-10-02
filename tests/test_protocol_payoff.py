# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""get_debt_payoff_plan through the MCP protocol: read-only, one YNAB request, two at most."""

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


def _account(key: str, name: str, kind: str, balance: float, **terms: Any) -> dict[str, Any]:
    return {
        "id": key,
        "name": name,
        "type": kind,
        "on_budget": kind in {"checking", "creditCard"},
        "closed": False,
        "balance": balance,
        "interest_rates": terms.get("rates", {}),
        "minimum_payments": terms.get("minimums", {}),
        "escrow_amounts": {},
    }


_ACCOUNTS = [
    _account("a-chk", "Checking", "checking", 2_400.0),
    _account("a-card", "Card", "creditCard", -600.0),
    _account(
        "a-car",
        "Car loan",
        "autoLoan",
        -1_200.0,
        rates={"2025-01-01": 12.0},
        minimums={"2025-01-01": 100.0},
    ),
]
_PAID = [
    {"account_id": "a-card", "date": f"2026-0{month}-28", "amount": 200_000}
    | {"transfer_account_id": "a-chk", "deleted": False}
    for month in (6, 7, 8)
]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[dict[str, AsyncMock]]:
    mocks = {
        "get_debt_terms": AsyncMock(return_value=_ACCOUNTS),
        "get_transactions": AsyncMock(return_value=_PAID),
    }
    with (
        patch("avenir_mcp.client.get_debt_terms", mocks["get_debt_terms"]),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
        patch("avenir_mcp.client.get_transactions", mocks["get_transactions"]),
    ):
        yield mocks


def test_debt_payoff_plan_is_read_only() -> None:
    """Declared read-only and idempotent: a client may call it without asking."""

    async def listed() -> dict[str, Any]:
        async with Client(server.mcp) as mcp_client:
            return {tool.name: tool.annotations for tool in await mcp_client.list_tools()}

    found = asyncio.run(listed())["get_debt_payoff_plan"]
    assert found.read_only_hint is True
    assert found.idempotent_hint is True
    assert found.open_world_hint is True


def test_a_given_budget_and_rate_need_one_request(ynab: dict[str, AsyncMock]) -> None:
    """The card's rate and minimum given, 400 a month: both strategies, no history read."""
    args = {
        "plan_id": "b1",
        "monthly_budget": 400,
        "overrides": [{"account": "card", "interest_rate": 24, "minimum_payment": 25}],
    }
    answer = call("get_debt_payoff_plan", args).structured_content
    assert [d["name"] for d in answer["debts"]] == ["Card", "Car loan"]
    assert answer["budget_from"] == "given"
    avalanche, snowball = answer["plans"]
    assert (avalanche["strategy"], snowball["strategy"]) == ("avalanche", "snowball")
    assert [d["name"] for d in avalanche["debts"]] == ["Card", "Car loan"]
    assert answer["interest_saved_by_avalanche"] == round(
        snowball["total_interest"] - avalanche["total_interest"], 2
    )
    assert ynab["get_debt_terms"].await_count == 1
    ynab["get_transactions"].assert_not_awaited()


def test_a_missing_minimum_reads_the_past_payments(ynab: dict[str, AsyncMock]) -> None:
    """No minimum for the card, no budget: 200 a month paid to it over the summer."""
    answer = call("get_debt_payoff_plan", {"plan_id": "b1", "strategy": "snowball"})
    data = answer.structured_content
    assert (data["monthly_budget"], data["budget_from"]) == (200.0, "past payments")
    assert [plan["strategy"] for plan in data["plans"]] == ["snowball"]
    assert ynab["get_transactions"].await_count == 1


def test_an_unknown_account_in_overrides_is_refused(ynab: dict[str, AsyncMock]) -> None:
    """The error lists the debts, so the agent can ask again."""
    args = {"plan_id": "b1", "overrides": [{"account": "Boat", "interest_rate": 5}]}
    answer = call("get_debt_payoff_plan", args)
    assert answer.is_error
    assert "'Boat'" in answer.content[0].text
    assert "Card, Car loan" in answer.content[0].text
    ynab["get_transactions"].assert_not_awaited()


def test_a_budget_below_the_minimums_is_refused(ynab: dict[str, AsyncMock]) -> None:
    """The car loan's 100 is owed anyway."""
    answer = call("get_debt_payoff_plan", {"plan_id": "b1", "monthly_budget": 50})
    assert answer.is_error
    assert "100.00" in answer.content[0].text
    ynab["get_transactions"].assert_not_awaited()


@pytest.mark.parametrize(
    "args",
    [
        {"strategy": "fastest"},
        {"monthly_budget": 0},
        {"monthly_budget": -10},
        {"max_months": 11},
        {"max_months": 1201},
        {"overrides": []},
        {"overrides": [{"account": ""}]},
        {"overrides": [{"account": "Card", "interest_rate": 101}]},
        {"overrides": [{"account": "Card", "minimum_payment": -1}]},
        {"overrides": [{"account": "Card", "rate": 5}]},
    ],
)
def test_arguments_out_of_range_are_refused_before_any_request(
    ynab: dict[str, AsyncMock], args: dict[str, Any]
) -> None:
    """Refused before YNAB is asked anything."""
    answer = call("get_debt_payoff_plan", {"plan_id": "b1", **args})
    assert answer.is_error
    assert all(mock.await_count == 0 for mock in ynab.values())


def test_the_schema_states_the_strategies_and_the_cap() -> None:
    """The agent sees the three strategies, both by default, and 600 months at most."""
    props = tool_schema("get_debt_payoff_plan")["properties"]
    assert props["strategy"]["enum"] == ["avalanche", "snowball", "both"]
    assert props["strategy"]["default"] == "both"
    cap = props["max_months"]
    assert (cap["minimum"], cap["maximum"], cap["default"]) == (12, 1200, 600)
