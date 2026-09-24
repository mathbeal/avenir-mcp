"""forecast_balance through the MCP protocol."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server

_ACCOUNTS = [
    {"id": "acc", "name": "Checking", "on_budget": True, "closed": False, "balance": 1000.0},
    {"id": "savings", "name": "Savings", "on_budget": True, "closed": False, "balance": 500.0},
    {"id": "old", "name": "Old", "on_budget": True, "closed": True, "balance": 0.0},
    {"id": "loan", "name": "Loan", "on_budget": False, "closed": False, "balance": -9000.0},
]
_TXS = [
    {
        "payee_name": "CAR LEASE",
        "amount": -400000,
        "date": f"2026-{m:02d}-25",
        "deleted": False,
        "transfer_account_id": None,
        "account_id": "acc",
    }
    for m in (5, 6, 7, 8)
] + [
    {
        "payee_name": "GYM",
        "amount": -30000,
        "date": f"2026-{m:02d}-03",
        "deleted": False,
        "transfer_account_id": None,
        "account_id": "savings",
    }
    for m in (5, 6, 7, 8)
]


@pytest.fixture(autouse=True, name="budget")
def _budget() -> Iterator[None]:
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=_TXS)),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 24)),
    ):
        yield


def _call(args: dict[str, Any]) -> Any:
    async def run() -> Any:
        async with Client(server.mcp) as mcp_client:
            return await mcp_client.call_tool("forecast_balance", args, raise_on_error=False)

    return asyncio.run(run())


def test_forecast_is_read_only() -> None:
    """A projection changes nothing."""

    async def run() -> Any:
        async with Client(server.mcp) as mcp_client:
            return next(t for t in await mcp_client.list_tools() if t.name == "forecast_balance")

    assert asyncio.run(run()).annotations.readOnlyHint is True


def test_forecast_uses_open_budget_accounts_and_shows_its_assumptions() -> None:
    """Start from open on-budget accounts; list the recurring charges it assumed."""
    data = _call({"budget_id": "b1", "until": "2026-11"}).structured_content
    assert data["accounts"] == ["Checking", "Savings"]
    assert data["start_balance"] == 1500.0
    assert {r["payee"] for r in data["assumptions"]["recurring"]} == {"CAR LEASE", "GYM"}
    assert data["assumptions"]["variable_monthly"] == 0.0
    assert [m["month"] for m in data["months"]] == ["2026-09", "2026-10", "2026-11"]
    assert data["months"][-1]["end"] == 1500.0 - 400.0 * 3 - 30.0 * 2


def test_forecast_can_be_limited_to_chosen_accounts() -> None:
    """account_ids narrows both the starting balance and the history."""
    data = _call(
        {"budget_id": "b1", "until": "2026-10", "account_ids": ["savings"]}
    ).structured_content
    assert data["start_balance"] == 500.0
    assert [r["payee"] for r in data["assumptions"]["recurring"]] == ["GYM"]


def test_caller_assumptions_override_and_add() -> None:
    """Income, variable spending and one-offs come from the caller when given."""
    data = _call(
        {
            "budget_id": "b1",
            "until": "2026-10",
            "monthly_income": 2000.0,
            "variable_monthly": -100.0,
            "one_offs": [{"date": "2026-10-15", "amount": -1426.0, "label": "property tax"}],
        }
    ).structured_content
    assert data["assumptions"]["variable_monthly"] == -100.0
    october = data["months"][1]
    assert october["inflows"] == 2000.0
    assert october["outflows"] == -100.0 - 400.0 - 30.0 - 1426.0


def test_shortfall_is_announced_in_the_message() -> None:
    """The first month the balance goes negative is said plainly."""
    data = _call({"budget_id": "b1", "until": "2027-03"}).structured_content
    assert data["first_shortfall"] == "2026-12"
    assert "2026-12" in data["message"]


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"until": "2026-13"}, "YYYY-MM"),
        ({"until": "2026-08"}, "current month"),
        ({"until": "2029-01"}, "24 months"),
        ({"until": "2026-10", "account_ids": ["nope"]}, "list_accounts"),
    ],
)
def test_invalid_request_is_a_tool_error(args: dict[str, Any], expected: str) -> None:
    """Bad horizon or account is refused with a way forward."""
    result = _call({"budget_id": "b1", **args})
    assert result.is_error
    assert expected in result.content[0].text


def test_income_defaults_to_recent_history() -> None:
    """Without monthly_income, the last 3 months' inflows are assumed, and shown."""
    invoices = [
        {
            "payee_name": f"CLIENT {m}",
            "amount": 1500000,
            "date": f"2026-{m:02d}-28",
            "deleted": False,
            "transfer_account_id": None,
            "account_id": "acc",
        }
        for m in (6, 7, 8)
    ]
    with patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=_TXS + invoices)):
        data = _call({"budget_id": "b1", "until": "2026-10"}).structured_content
    assert data["assumptions"]["monthly_income"] == 1500.0
    assert data["months"][1]["inflows"] == 1500.0


def test_current_month_deducts_what_already_happened() -> None:
    """Spending already made this month is not projected again."""
    spent = {
        "payee_name": "TAX",
        "amount": -100000,
        "date": "2026-09-10",
        "deleted": False,
        "transfer_account_id": None,
        "account_id": "acc",
    }
    past = [dict(spent, date=f"2026-{m:02d}-10", payee_name=f"SHOP {m}") for m in (6, 7, 8)]
    with patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=_TXS + past + [spent])):
        data = _call({"budget_id": "b1", "until": "2026-09"}).structured_content
    assert data["assumptions"]["variable_monthly"] == -100.0
    assert data["months"][0]["outflows"] == -400.0
