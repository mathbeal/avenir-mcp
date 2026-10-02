# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for savings.py: how much of the income was kept, month by month."""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp import savings


def _account(key: str, kind: str, *, tracking: bool = False) -> dict[str, Any]:
    """An account as client.get_accounts gives it, named after its id."""
    return {"id": key, "name": key.title(), "type": kind, "balance": 0.0} | {
        "on_budget": not tracking,
        "closed": False,
    }


TODAY = date(2026, 9, 25)

ACCOUNTS = [
    _account("checking", "checking"),
    _account("savings", "savings"),
    _account("card", "creditCard"),
    _account("brokerage", "otherAsset", tracking=True),
    _account("joint", "savings", tracking=True),
    _account("mortgage", "mortgage", tracking=True),
]

CATEGORIES = [
    {"id": "cat-inflow", "name": "Inflow: Ready to Assign"}
    | {"category_group_name": "Internal Master Category"},
    {"id": "cat-none", "name": "Uncategorized", "category_group_name": "Internal Master Category"},
    {"id": "cat-rent", "name": "Rent", "category_group_name": "Bills"},
    {"id": "cat-food", "name": "Groceries", "category_group_name": "Everyday"},
]


def _tx(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    account: str,
    day: str,
    amount: int,
    category: str | None = None,
    transfer: str | None = None,
    deleted: bool = False,
    lines: list[dict[str, Any]] | None = None,
    payee: str = "Someone",
) -> dict[str, Any]:
    return {
        "account_id": account,
        "date": day,
        "amount": amount,
        "payee_name": payee,
        "category_id": category,
        "transfer_account_id": transfer,
        "deleted": deleted,
        "subtransactions": lines or [],
    }


def _salary_and_rent(
    salary: int = 3_000_000, rent: int = -1_000_000, months: tuple[str, ...] = ("06", "07", "08")
) -> list[dict[str, Any]]:
    """A salary and a rent payment on the checking account in each month."""
    return [
        tx
        for m in months
        for tx in (
            _tx("checking", f"2026-{m}-28", salary, "cat-inflow"),
            _tx("checking", f"2026-{m}-03", rent, "cat-rent"),
        )
    ]


def _summary(history: list[dict[str, Any]], months: int = 3, today: date = TODAY) -> Any:
    return savings.summary(ACCOUNTS, CATEGORIES, history, today, months)


def test_the_rate_is_what_was_kept_of_the_income_to_one_decimal() -> None:
    """3,000 in and 1,000 out each month: 2,000 saved, 66.7 %."""
    answer = _summary(_salary_and_rent())
    assert [m.month for m in answer.months] == ["2026-06", "2026-07", "2026-08"]
    first = answer.months[0]
    assert (first.income, first.spending, first.saved, first.rate) == (
        3_000.0,
        -1_000.0,
        2_000.0,
        66.7,
    )
    assert (answer.income, answer.spending, answer.saved, answer.rate) == (
        9_000.0,
        -3_000.0,
        6_000.0,
        66.7,
    )
    assert answer.average_saved == 2_000.0
    assert "66.7 %" in answer.message


def test_best_and_worst_months_are_named() -> None:
    """A dearer July is the worst month, a cheaper August the best."""
    history = [
        *_salary_and_rent(),
        _tx("card", "2026-07-15", -1_400_000, "cat-food"),
        _tx("checking", "2026-08-20", 400_000, "cat-inflow"),
    ]
    answer = _summary(history)
    assert [m.rate for m in answer.months] == [66.7, 20.0, 70.6]
    assert (answer.best_month, answer.worst_month) == ("2026-08", "2026-07")
    assert "Best month: 2026-08 (70.6 %), worst: 2026-07 (20.0 %)" in answer.message


def test_a_refund_reduces_spending_and_is_not_income() -> None:
    """60 back on groceries: spending falls to 940, income stays 3,000."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("card", "2026-08-12", 60_000, "cat-food"),
    ]
    month = _summary(history, months=1).months[0]
    assert (month.income, month.spending, month.saved) == (3_000.0, -940.0, 2_060.0)


def test_transfers_between_budget_accounts_are_neither_income_nor_spending() -> None:
    """Money put into budget savings and a card paid off stay in the budget."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("checking", "2026-08-29", -500_000, transfer="savings"),
        _tx("savings", "2026-08-29", 500_000, "cat-inflow", transfer="checking"),
        _tx("checking", "2026-08-30", -200_000, transfer="card"),
        _tx("card", "2026-08-30", 200_000, transfer="checking"),
    ]
    month = _summary(history, months=1).months[0]
    assert (month.income, month.spending) == (3_000.0, -1_000.0)


def test_a_transfer_to_an_asset_tracking_account_is_saved_not_spent() -> None:
    """300 to the brokerage and 200 to the joint savings are saved; 400 to the mortgage is not."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("checking", "2026-08-05", -300_000, "cat-food", transfer="brokerage"),
        _tx("brokerage", "2026-08-05", 300_000, transfer="checking"),
        _tx("checking", "2026-08-06", -200_000, transfer="joint"),
        _tx("checking", "2026-08-07", -400_000, "cat-rent", transfer="mortgage"),
    ]
    answer = _summary(history, months=1)
    month = answer.months[0]
    assert (month.income, month.spending, month.saved) == (3_000.0, -1_400.0, 1_600.0)
    assert answer.moved_to_tracking == 500.0
    assert any("tracking account that holds an asset" in note for note in answer.notes)


def test_money_back_from_a_tracking_account_is_not_income() -> None:
    """1,000 taken back from the brokerage into checking, given Ready to Assign: not income."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("checking", "2026-08-09", 1_000_000, "cat-inflow", transfer="brokerage"),
        _tx("checking", "2026-08-10", 1_000_000, "cat-food", transfer="joint"),
    ]
    month = _summary(history, months=1).months[0]
    assert (month.income, month.spending) == (3_000.0, -1_000.0)


def test_starting_balances_and_uncategorised_inflows_are_not_income() -> None:
    """A starting balance is money already there; an inflow without a category is noted."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("savings", "2026-08-01", 5_000_000, "cat-inflow", payee="Starting Balance"),
        _tx("checking", "2026-08-14", 75_000),
        _tx("checking", "2026-08-15", 25_000, "cat-none"),
    ]
    answer = _summary(history, months=1)
    assert answer.months[0].income == 3_000.0
    assert answer.months[0].spending == -1_000.0
    assert any("2 inflows without a category (100.00)" in note for note in answer.notes)


def test_tracking_accounts_and_deleted_transactions_are_left_out() -> None:
    """What happens inside a tracking account, or was deleted, is not the budget's."""
    history = [
        *_salary_and_rent(months=("08",)),
        _tx("joint", "2026-08-15", 1_600_000, payee="Tax refund"),
        _tx("brokerage", "2026-08-16", -50_000),
        _tx("checking", "2026-08-17", -999_000, "cat-food", deleted=True),
        _tx("gone", "2026-08-18", -1_000_000),
    ]
    month = _summary(history, months=1).months[0]
    assert (month.income, month.spending) == (3_000.0, -1_000.0)


def test_a_split_counts_each_line_on_its_own() -> None:
    """One deposit: 2,500 salary, 100 refund of groceries; one payment: rent and savings."""
    deposit: list[dict[str, Any]] = [
        {"amount": 2_500_000, "category_id": "cat-inflow", "transfer_account_id": None},
        {"amount": 100_000, "category_id": "cat-food", "transfer_account_id": None},
        {"amount": 999_000, "category_id": "cat-inflow", "deleted": True},
    ]
    payment: list[dict[str, Any]] = [
        {"amount": -1_000_000, "category_id": "cat-rent", "transfer_account_id": None},
        {"amount": -300_000, "category_id": None, "transfer_account_id": "brokerage"},
    ]
    history = [
        _tx("checking", "2026-08-28", 2_600_000, lines=deposit),
        _tx("checking", "2026-08-03", -1_300_000, lines=payment),
    ]
    month = _summary(history, months=1).months[0]
    assert (month.income, month.spending, month.saved) == (2_500.0, -900.0, 1_600.0)


def test_a_month_without_income_has_no_rate() -> None:
    """September spent 500 with no salary yet: saved -500, rate null, not a division by zero."""
    history = [*_salary_and_rent(), _tx("checking", "2026-09-03", -500_000, "cat-rent")]
    answer = _summary(history, months=4, today=date(2026, 10, 2))
    september = answer.months[-1]
    assert (september.income, september.saved, september.rate) == (0.0, -500.0, None)
    assert answer.worst_month == "2026-06"
    assert answer.rate == round(5_500 / 9_000 * 100, 1)
    assert any("2026-09" in note and "no income" in note for note in answer.notes)


def test_spending_above_income_gives_a_negative_rate() -> None:
    """1,000 in, 1,250 out: -25.0 %."""
    month = _summary(_salary_and_rent(1_000_000, -1_250_000, ("08",)), months=1).months[0]
    assert (month.saved, month.rate) == (-250.0, -25.0)


def test_without_any_income_no_rate_is_given() -> None:
    """Spending only: the answer says no rate can be given."""
    answer = _summary([_tx("checking", "2026-08-03", -100_000, "cat-rent")])
    assert answer.rate is None
    assert (answer.best_month, answer.worst_month) == (None, None)
    assert "No income" in answer.message


def test_months_before_the_first_transaction_are_not_counted() -> None:
    """Six months asked, history since July: July and August only, and a note says so."""
    answer = _summary(_salary_and_rent(months=("07", "08")), months=6)
    assert [m.month for m in answer.months] == ["2026-07", "2026-08"]
    assert any("Only the last 2 of the 6 months" in note for note in answer.notes)


def test_without_any_history_nothing_is_measured() -> None:
    """A new plan: no complete month yet, and the answer says so."""
    answer = _summary([])
    assert answer.months == []
    assert answer.rate is None
    assert answer.average_saved == 0.0
    assert "No complete month" in answer.message


def test_every_answer_states_its_rules() -> None:
    """Refunds, transfers and what counts as saving are said in plain words."""
    notes = " ".join(_summary(_salary_and_rent()).notes)
    assert "Ready to Assign" in notes
    assert "refund" in notes
    assert "transfers between budget accounts" in notes
    assert "loan" in notes
