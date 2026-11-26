# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Previews respect the plan's currency: no more hidden rounding, no more silent zero moves."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from .fake_month import FakeMonth, serving
from .mcp_helpers import asking, call

EUR = {"decimal_digits": 2}
BHD = {"decimal_digits": 3}
JPY = {"decimal_digits": 0}


@pytest.fixture(name="month")
def _month(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeMonth]:
    fake = FakeMonth(
        {"c-food": "Restaurants", "c-fun": "Tennis"}, {"c-food": 120000, "c-fun": 80000}
    )
    with serving(fake, tmp_path, monkeypatch):
        yield fake


def _currency(currency_format: dict[str, int]) -> Any:
    return patch("avenir_mcp.client.get_currency_format", AsyncMock(return_value=currency_format))


def test_a_budget_amount_the_currency_cannot_hold_is_refused(month: FakeMonth) -> None:
    """80.004 is not a whole number of cents: refused, not silently shown as 80.00 -> 80.00."""
    args = {"plan_id": "b1", "month": "2026-09-01", "category_id": "c-fun", "amount": 80.004}
    with _currency(EUR):
        result = call("set_category_budget", args)
    assert result.is_error
    assert "decimal digit" in result.content[0].text
    assert not month.sets


def test_a_budget_amount_the_currency_holds_is_shown_at_its_own_precision(
    month: FakeMonth,
) -> None:
    """A three-decimal currency (e.g. the Bahraini dinar) shows three decimals, not two."""
    month.budgeted["c-fun"] = 1234
    asked: list[str] = []
    args = {"plan_id": "b1", "month": "2026-09-01", "category_id": "c-fun", "amount": 1.239}
    with _currency(BHD):
        call("set_category_budget", args, asking(asked))
    assert asked == ["Budget Tennis for 2026-09-01: 1.234 → 1.239?"]
    assert month.sets == [("2026-09-01", "c-fun", 1.239)]


@pytest.mark.usefixtures("month")
def test_a_budget_amount_in_a_currency_with_no_decimals_is_shown_whole() -> None:
    """A currency without fractional units (e.g. the yen) shows a whole number, not '.00'."""
    asked: list[str] = []
    args = {"plan_id": "b1", "month": "2026-09-01", "category_id": "c-fun", "amount": 90.0}
    with _currency(JPY):
        call("set_category_budget", args, asking(asked))
    assert asked == ["Budget Tennis for 2026-09-01: 80 → 90?"]


MOVE = {
    "plan_id": "b1",
    "month": "2026-09-01",
    "from_category_id": "c-fun",
    "to_category_id": "c-food",
}


def test_a_move_the_currency_cannot_hold_is_refused_instead_of_shown_as_zero(
    month: FakeMonth,
) -> None:
    """0.004 in a two-decimal currency is refused: no more 'Move 0.00' while 4 milliunits move."""
    asked: list[str] = []
    with _currency(EUR):
        result = call("move_money", {**MOVE, "amount": 0.004}, asking(asked))
    assert result.is_error
    assert "decimal digit" in result.content[0].text
    assert not asked
    assert month.budgeted == {"c-food": 120000, "c-fun": 80000}


def test_a_move_below_the_milliunit_is_refused_instead_of_applied_as_nothing(
    month: FakeMonth,
) -> None:
    """0.0004 used to round to 0 milliunits and still apply: now refused, in any currency."""
    with _currency(BHD):
        result = call("move_money", {**MOVE, "amount": 0.0004}, asking([]))
    assert result.is_error
    assert "decimal digit" in result.content[0].text
    assert month.budgeted == {"c-food": 120000, "c-fun": 80000}


def test_a_move_the_currency_holds_exactly_is_shown_at_its_own_precision(
    month: FakeMonth,
) -> None:
    """0.004 is a whole number of thousandths of a dinar: moved, and shown as such."""
    asked: list[str] = []
    with _currency(BHD):
        call("move_money", {**MOVE, "amount": 0.004}, asking(asked))
    assert asked[0].startswith("Move 0.004 from Tennis to Restaurants")
    assert month.budgeted == {"c-food": 120004, "c-fun": 79996}


_BANK_ACCOUNTS = [{"id": "acc", "name": "Checking"}]
_BANK_CATS = [
    {
        "id": "c-inflow",
        "name": "Inflow: Ready to Assign",
        "category_group_name": "Internal Master Category",
    }
]


class _Bank:  # pylint: disable=too-few-public-methods
    """A fake account with one cleared transaction."""

    def __init__(self) -> None:
        self.transactions: list[dict[str, Any]] = [
            {
                "id": "t1",
                "amount": -30000,
                "cleared": "cleared",
                "account_id": "acc",
                "payee_name": "Market",
                "date": "2026-09-11",
                "deleted": False,
            }
        ]

    async def get_transactions(self, _plan_id: str) -> list[dict[str, Any]]:
        """Copies, as YNAB would return them."""
        return [dict(tx) for tx in self.transactions]


@pytest.fixture(name="bank")
def _bank() -> Iterator[_Bank]:
    fake = _Bank()
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_BANK_ACCOUNTS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_BANK_CATS)),
        patch("avenir_mcp.client.get_transactions", fake.get_transactions),
    ):
        yield fake


@pytest.mark.usefixtures("bank")
def test_a_bank_balance_the_currency_cannot_hold_is_refused() -> None:
    """A balance of a thousandth of a euro cannot become a balance adjustment: refused."""
    args = {"plan_id": "b1", "account_id": "acc", "bank_balance": 65.004, "adjust": True}
    with _currency(EUR):
        result = call("reconcile_account", args)
    assert result.is_error
    assert "decimal digit" in result.content[0].text


def test_a_new_transaction_amount_the_currency_cannot_hold_is_refused() -> None:
    """A transaction amount with a thousandth of a euro is refused before anything is asked."""
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_BANK_ACCOUNTS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=[])),
        _currency(EUR),
    ):
        result = call(
            "create_transactions",
            {
                "plan_id": "b1",
                "account_id": "acc",
                "transactions": [{"date": "2026-09-01", "amount": -12.345, "payee_name": "Shop"}],
            },
        )
    assert result.is_error
    assert "decimal digit" in result.content[0].text


_SPLIT_TX = {
    "id": "t1",
    "account_id": "acc",
    "date": "2026-09-12",
    "amount": -1234,
    "payee_name": "Repair shop",
    "category_id": None,
    "transfer_account_id": None,
    "subtransactions": [],
}
_SPLIT_CATS = [{"id": "c-food", "name": "Groceries"}, {"id": "c-home", "name": "Household"}]


def test_a_mismatched_split_shows_the_two_totals_at_the_currencys_own_precision() -> None:
    """A split short by three thousandths of a dinar no longer looks identical at two decimals."""
    with (
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=[_SPLIT_TX])),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_SPLIT_CATS)),
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=[])),
        _currency(BHD),
    ):
        result = call(
            "split_transaction",
            {
                "plan_id": "b1",
                "transaction_id": "t1",
                "lines": [
                    {"amount": -1.000, "category_id": "c-food"},
                    {"amount": -0.231, "category_id": "c-home"},
                ],
            },
        )
    assert result.is_error
    assert "The lines add up to -1.231, the transaction is -1.234" in result.content[0].text


def test_a_split_line_the_currency_cannot_hold_is_refused() -> None:
    """A split line of a thousandth of a euro is refused, not silently rounded away."""
    with (
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=[_SPLIT_TX])),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_SPLIT_CATS)),
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=[])),
        _currency(EUR),
    ):
        result = call(
            "split_transaction",
            {
                "plan_id": "b1",
                "transaction_id": "t1",
                "lines": [
                    {"amount": -1.2335, "category_id": "c-food"},
                    {"amount": -0.0005, "category_id": "c-home"},
                ],
            },
        )
    assert result.is_error
    assert "decimal digit" in result.content[0].text
