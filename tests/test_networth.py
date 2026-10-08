# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for networth.py: what a plan owns and owes at the end of each month."""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp import networth

TODAY = date(2026, 9, 25)


def _account(acc_id: str, kind: str, balance: float, closed: bool = False) -> dict[str, Any]:
    return {
        "id": acc_id,
        "name": acc_id.title(),
        "type": kind,
        "on_budget": kind in ("checking", "creditCard"),
        "closed": closed,
        "balance": balance,
    }


def _tx(account: str, day: str, amount: int, deleted: bool = False) -> dict[str, Any]:
    return {"account_id": account, "date": day, "amount": amount, "deleted": deleted}


def test_each_month_end_is_todays_balance_less_what_came_later() -> None:
    """A salary of 2,000 on 28 August: the end of July is 2,000 lower than August."""
    accounts = [_account("checking", "checking", 3_000.0)]
    answer = networth.trend(accounts, [_tx("checking", "2026-08-28", 2_000_000)], TODAY, 3)
    assert [(m.month, m.assets, m.debts, m.net_worth) for m in answer.months] == [
        ("2026-07-01", 1_000.0, 0.0, 1_000.0),
        ("2026-08-01", 3_000.0, 0.0, 3_000.0),
        ("2026-09-01", 3_000.0, 0.0, 3_000.0),
    ]


def test_debts_are_negative_and_net_worth_adds_them_to_the_assets() -> None:
    """A loan paid 300 a month comes down; the net worth rises with it."""
    accounts = [
        _account("checking", "checking", 1_200.0),
        _account("loan", "autoLoan", -9_400.0),
        _account("card", "creditCard", -250.5),
    ]
    payments = [
        _tx(account, f"2026-0{month}-10", amount)
        for month in (8, 9)
        for account, amount in (("checking", -300_000), ("loan", 300_000))
    ]
    answer = networth.trend(accounts, payments, TODAY, 2)
    assert [(m.assets, m.debts, m.net_worth) for m in answer.months] == [
        (1_500.0, -9_950.5, -8_450.5),
        (1_200.0, -9_650.5, -8_450.5),
    ]


def test_account_types_decide_assets_and_debts_whatever_the_sign() -> None:
    """An overdrawn checking account stays an asset; a card paid beyond its balance, a debt."""
    accounts = [
        *(_account(kind, kind, 10.0) for kind in sorted(networth.DEBT_TYPES)),
        *(_account(kind, kind, -1.0) for kind in ("checking", "savings", "cash", "otherAsset")),
    ]
    [month] = networth.trend(accounts, [], TODAY, 1).months
    assert (month.assets, month.debts, month.net_worth) == (-4.0, 90.0, 86.0)


def test_months_cross_the_new_year_oldest_first() -> None:
    """Four months back from February: November to February."""
    answer = networth.trend([], [], date(2027, 2, 3), 4)
    assert [m.month for m in answer.months] == [
        "2026-11-01",
        "2026-12-01",
        "2027-01-01",
        "2027-02-01",
    ]


def test_a_closed_account_counts_while_it_had_a_balance() -> None:
    """A student loan paid off in July and closed: in July's figures, gone from September's."""
    accounts = [
        _account("checking", "checking", 500.0),
        _account("student", "studentLoan", 0.0, closed=True),
    ]
    last = [_tx("student", "2026-08-10", 250_000), _tx("checking", "2026-08-10", -250_000)]
    answer = networth.trend(accounts, last, TODAY, 3)
    assert [m.debts for m in answer.months] == [-250.0, 0.0, 0.0]
    assert answer.accounts == ["Checking", "Student"]
    recent = networth.trend(accounts, last, TODAY, 1)
    assert recent.accounts == ["Checking"]


def test_deleted_transactions_and_unknown_accounts_change_nothing() -> None:
    """A deleted transaction, and one of an account deleted since, leave the balances alone.

    Both fall after the end of August, where they would otherwise count, and both come
    before a transaction that does: skipping one cannot mean stopping at it.
    """
    accounts = [_account("checking", "checking", 100.0)]
    mixed = [
        _tx("checking", "2026-09-10", 50_000, deleted=True),
        _tx("gone", "2026-09-11", 1),
        _tx("checking", "2026-09-12", 20_000),
    ]
    assert [m.assets for m in networth.trend(accounts, mixed, TODAY, 2).months] == [80.0, 100.0]


def test_a_transaction_dated_the_first_of_a_month_belongs_to_that_month() -> None:
    """The end of August is before 1 September: money moved that day is taken off it."""
    accounts = [_account("checking", "checking", 100.0)]
    first = [_tx("checking", "2026-09-01", 10_000)]
    assert [m.assets for m in networth.trend(accounts, first, TODAY, 2).months] == [90.0, 100.0]


def test_everything_that_came_later_is_taken_off_the_month_end() -> None:
    """Two payments after the end of August come off it, not just the last one."""
    accounts = [_account("checking", "checking", 100.0)]
    later = [_tx("checking", "2026-09-12", 20_000), _tx("checking", "2026-09-13", 5_000)]
    assert [m.assets for m in networth.trend(accounts, later, TODAY, 2).months] == [75.0, 100.0]


def test_the_summary_says_where_the_net_worth_started_and_ended() -> None:
    """From -1,000 to 500: a change of 1,500 over the months shown."""
    accounts = [_account("checking", "checking", 1_500.0), _account("card", "creditCard", -1_000.0)]
    income = [_tx("checking", "2026-09-05", 1_500_000)]
    answer = networth.trend(accounts, income, TODAY, 2)
    assert (answer.first_net_worth, answer.last_net_worth, answer.change) == (
        -1_000.0,
        500.0,
        1_500.0,
    )
