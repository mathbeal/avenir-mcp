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

from .factories import scheduled

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
def _budget() -> Iterator[AsyncMock]:
    """A fake YNAB on 24 September 2026, with no schedule unless a test gives some."""
    schedules = AsyncMock(return_value=[])
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=_TXS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=[])),
        patch("avenir_mcp.client.get_scheduled_transactions", schedules),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 24)),
    ):
        yield schedules


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

    assert asyncio.run(run()).annotations.read_only_hint is True


def test_forecast_uses_open_budget_accounts_and_shows_its_assumptions() -> None:
    """Start from open on-budget accounts; list the recurring charges it assumed."""
    data = _call({"plan_id": "b1", "until": "2026-11"}).structured_content
    assert data["accounts"] == ["Checking", "Savings"]
    assert data["start_balance"] == 1500.0
    assert {r["payee"] for r in data["assumptions"]["recurring"]} == {"CAR LEASE", "GYM"}
    assert data["assumptions"]["variable_monthly"] == 0.0
    assert [m["month"] for m in data["months"]] == ["2026-09", "2026-10", "2026-11"]
    assert data["months"][-1]["end"] == 1500.0 - 400.0 * 3 - 30.0 * 2


def test_forecast_can_be_limited_to_chosen_accounts() -> None:
    """account_ids narrows both the starting balance and the history."""
    data = _call(
        {"plan_id": "b1", "until": "2026-10", "account_ids": ["savings"]}
    ).structured_content
    assert data["start_balance"] == 500.0
    assert [r["payee"] for r in data["assumptions"]["recurring"]] == ["GYM"]


def test_caller_assumptions_override_and_add() -> None:
    """Income, variable spending and one-offs come from the caller when given."""
    data = _call(
        {
            "plan_id": "b1",
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
    data = _call({"plan_id": "b1", "until": "2027-03"}).structured_content
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
    result = _call({"plan_id": "b1", **args})
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
        data = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
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
        data = _call({"plan_id": "b1", "until": "2026-09"}).structured_content
    assert data["assumptions"]["variable_monthly"] == -100.0
    assert data["months"][0]["outflows"] == -400.0


def test_given_income_replaces_income_found_in_history() -> None:
    """A salary recurring in the history is not counted on top of monthly_income."""
    salary = [
        {
            "payee_name": "EMPLOYER",
            "amount": 3200000,
            "date": f"2026-{m:02d}-28",
            "deleted": False,
            "transfer_account_id": None,
            "account_id": "acc",
        }
        for m in (5, 6, 7, 8)
    ]
    with patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=_TXS + salary)):
        data = _call({"plan_id": "b1", "until": "2026-10", "monthly_income": 3200.0})
    content = data.structured_content
    assert content["months"][1]["inflows"] == 3200.0
    assert all(r["amount"] < 0 for r in content["assumptions"]["recurring"])


def _outflows(data: dict[str, Any], month: str) -> float:
    return float(next(m["outflows"] for m in data["months"] if m["month"] == month))


def test_a_scheduled_payment_falls_on_its_date(budget: AsyncMock) -> None:
    """A yearly bill the history cannot guess is projected, and listed in the assumptions."""
    before = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    budget.return_value = [
        scheduled(
            "HOME INSURANCE", "2025-10-20", "2026-10-20", "yearly", amount=-420_000,
            category_id=None,
        )
    ]  # fmt: skip
    after = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    assert [o["payee"] for o in after["assumptions"]["scheduled"]] == ["HOME INSURANCE"]
    assert round(_outflows(after, "2026-10") - _outflows(before, "2026-10"), 2) == -420.0


def test_a_charge_with_a_schedule_is_not_counted_twice(budget: AsyncMock) -> None:
    """The schedule replaces what the history guessed for the same payee: same months."""
    before = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    budget.return_value = [
        scheduled("CAR LEASE", "2026-01-25", "2026-09-25", "monthly", amount=-400_000)
    ]
    after = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    assert "CAR LEASE" not in [r["payee"] for r in after["assumptions"]["recurring"]]
    assert [o["date"] for o in after["assumptions"]["scheduled"]] == ["2026-09-25", "2026-10-25"]
    for month in ("2026-09", "2026-10"):
        assert _outflows(after, month) == _outflows(before, month)


def test_transfers_between_projected_accounts_cancel(budget: AsyncMock) -> None:
    """Money moved from Checking to Savings leaves neither when both are projected."""
    budget.return_value = [
        scheduled(
            "Transfer : Savings", "2026-01-29", "2026-09-29", "monthly", amount=-200_000,
            category_id=None, transfer_account_id="savings",
        )
    ]  # fmt: skip
    both = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    assert both["assumptions"]["scheduled"] == []
    alone = _call({"plan_id": "b1", "until": "2026-10", "account_ids": ["acc"]}).structured_content
    assert [o["amount"] for o in alone["assumptions"]["scheduled"]] == [-200.0, -200.0]


def test_schedules_of_other_accounts_are_left_out(budget: AsyncMock) -> None:
    """Only the projected accounts' schedules count."""
    budget.return_value = [
        scheduled("LOAN PAYMENT", "2026-01-05", "2026-10-05", "monthly", account_id="loan")
    ]
    data = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    assert data["assumptions"]["scheduled"] == []


def _inflows(data: dict[str, Any], month: str) -> float:
    return float(next(m["inflows"] for m in data["months"] if m["month"] == month))


def test_given_income_replaces_scheduled_income(budget: AsyncMock) -> None:
    """A salary scheduled in YNAB is not added to the income the caller gives."""
    budget.return_value = [
        scheduled("ACME SALARY", "2026-01-28", "2026-09-28", "monthly", amount=2_500_000),
        scheduled("GYM", "2026-01-26", "2026-09-26", "monthly", amount=-30_000, id="s2"),
    ]
    data = _call({"plan_id": "b1", "until": "2026-10", "monthly_income": 3000}).structured_content
    assert [o["payee"] for o in data["assumptions"]["scheduled"]] == ["GYM", "GYM"]
    assert round(_inflows(data, "2026-10"), 2) == 3000.0


def test_a_schedule_named_briefly_still_replaces_the_bank_payee(budget: AsyncMock) -> None:
    """A schedule "Lease" covers the bank's "CAR LEASE": the charge is not counted twice."""
    before = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    budget.return_value = [
        scheduled("Lease", "2026-01-25", "2026-09-25", "monthly", amount=-400_000)
    ]
    after = _call({"plan_id": "b1", "until": "2026-10"}).structured_content
    assert "CAR LEASE" not in [r["payee"] for r in after["assumptions"]["recurring"]]
    for month in ("2026-09", "2026-10"):
        assert _outflows(after, month) == _outflows(before, month)
