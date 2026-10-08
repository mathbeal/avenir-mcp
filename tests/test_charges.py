# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for charges.py: the recurring charges a plan pays, and what they cost over a year."""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp import charges

TODAY = date(2026, 9, 24)
MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08"]
CATEGORIES = [
    {"id": "c-subs", "name": "Subscriptions"},
    {"id": "c-rent", "name": "Rent"},
    {"id": "c-inflow", "name": "Inflow: Ready to Assign"},
]


def _tx(payee: str, amount: int, day: str, category: str | None = None) -> dict[str, Any]:
    return {
        "payee_name": payee,
        "amount": amount,
        "date": day,
        "category_id": category,
        "deleted": False,
        "transfer_account_id": None,
        "account_id": "acc",
    }


def _monthly(payee: str, amount: int, day: int, category: str | None) -> list[dict[str, Any]]:
    return [_tx(payee, amount, f"{m}-{day:02d}", category) for m in MONTHS]


PLAN = (
    _monthly("STREAMFLIX", -13_490, 15, "c-subs")
    + _monthly("LANDLORD SARL", -950_000, 3, "c-rent")
    + _monthly("ACME EMPLOYER SALAIRE", 3_200_000, 28, "c-inflow")
    + [_tx("CORNER SHOP", -12_000, "2026-06-10")]
)


def test_a_monthly_charge_is_found_with_its_cost_over_a_year() -> None:
    """Streaming at 13.49 a month: 161.88 a year, the category it goes to, the day it falls on."""
    found = charges.find(PLAN, [], CATEGORIES, TODAY)
    stream = next(c for c in found.charges if c.payee == "STREAMFLIX")
    assert stream.monthly_amount == -13.49
    assert stream.yearly_amount == -161.88
    assert stream.category == "Subscriptions"
    assert stream.day == 15
    assert stream.months_seen == 4
    assert stream.scheduled is False


def test_a_transaction_without_a_payee_names_no_charge() -> None:
    """A payment YNAB names no payee for cannot be a recurring charge, nor decide a category."""
    blank = [_tx(None, -20_000, f"{m}-07", "c-subs") for m in MONTHS]  # type: ignore[arg-type]
    found = charges.find(PLAN + blank, [], CATEGORIES, TODAY)
    assert [c.payee for c in found.charges] == ["LANDLORD SARL", "STREAMFLIX"]


def test_the_costliest_over_a_year_comes_first_and_the_total_adds_them_up() -> None:
    """Rent before streaming; a one-off purchase is not a recurring charge."""
    found = charges.find(PLAN, [], CATEGORIES, TODAY)
    assert [c.payee for c in found.charges] == ["LANDLORD SARL", "STREAMFLIX"]
    assert found.yearly_total == -11_561.88


def test_income_is_left_out_unless_asked_for() -> None:
    """A salary recurs too; it is listed, after the charges, only with include_income."""
    found = charges.find(PLAN, [], CATEGORIES, TODAY, include_income=True)
    assert [c.payee for c in found.charges][-1] == "ACME EMPLOYER SALAIRE"
    assert found.charges[-1].yearly_amount == 38_400.0
    assert found.yearly_total == -11_561.88


def test_a_charge_a_schedule_already_covers_says_so() -> None:
    """A YNAB schedule for the landlord marks the rent as scheduled; streaming is not."""
    rent_schedule = {"payee_name": "Landlord SARL", "amount": -950_000, "deleted": False}
    found = charges.find(PLAN, [rent_schedule], CATEGORIES, TODAY)
    assert {c.payee: c.scheduled for c in found.charges} == {
        "LANDLORD SARL": True,
        "STREAMFLIX": False,
    }


def test_a_deleted_schedule_covers_nothing() -> None:
    """Only schedules still in YNAB count."""
    gone = {"payee_name": "STREAMFLIX", "amount": -13_490, "deleted": True}
    found = charges.find(PLAN, [gone], CATEGORIES, TODAY)
    assert not any(c.scheduled for c in found.charges)


def test_a_charge_never_categorised_has_no_category() -> None:
    """Without a category, the answer says null rather than guess."""
    plan = _monthly("GYM CLUB", -30_000, 5, None)
    [gym] = charges.find(plan, [], CATEGORIES, TODAY).charges
    assert gym.category is None


def test_the_most_frequent_category_wins() -> None:
    """Three months in Subscriptions, one elsewhere: Subscriptions."""
    plan = _monthly("STREAMFLIX", -13_490, 15, "c-subs")
    plan[0]["category_id"] = "c-rent"
    [stream] = charges.find(plan, [], CATEGORIES, TODAY).charges
    assert stream.category == "Subscriptions"


# ---------------------------------------------------------------------------
# Cases found by mutation testing
# ---------------------------------------------------------------------------


def test_a_category_outside_the_months_looked_at_does_not_decide() -> None:
    """Only the four full months count: this month's categories have no say yet."""
    plan = _monthly("STREAMFLIX", -13_490, 15, "c-subs")
    plan += [_tx("STREAMFLIX", -13_490, f"2026-09-{day:02d}", "c-rent") for day in (1, 2, 3, 4, 5)]
    [stream] = charges.find(plan, [], CATEGORIES, TODAY).charges
    assert stream.category == "Subscriptions"


def test_a_transfer_does_not_decide_the_category() -> None:
    """A transfer is not money leaving the plan: its category says nothing about a charge."""
    plan = _monthly("STREAMFLIX", -13_490, 15, "c-subs")
    moved = [
        dict(_tx("STREAMFLIX", -13_490, f"{month}-16", "c-rent"), transfer_account_id="acc-savings")
        for month in MONTHS
        for _ in range(2)
    ]
    [stream] = charges.find(plan + moved, [], CATEGORIES, TODAY).charges
    assert stream.category == "Subscriptions"


def test_the_yearly_amount_and_the_total_are_rounded_to_the_cent() -> None:
    """Twelve times 1.234 is 14.808: the answer says 14.81, as money is written."""
    plan = _monthly("WATER BOARD", -1_234, 8, None)
    found = charges.find(plan, [], CATEGORIES, TODAY)
    assert [c.yearly_amount for c in found.charges] == [-14.81]
    assert found.yearly_total == -14.81


def test_income_comes_from_the_largest_down() -> None:
    """The biggest income over a year first, the other way round from the charges."""
    plan = _monthly("SMALL RENT INCOME", 120_000, 4, None) + _monthly(
        "BIG SALARY", 3_200_000, 28, None
    )
    found = charges.find(plan, [], CATEGORIES, TODAY, include_income=True)
    assert [c.payee for c in found.charges] == ["BIG SALARY", "SMALL RENT INCOME"]


def test_income_of_less_than_a_unit_is_still_income() -> None:
    """Interest of 50 cents a month is listed with the income, not with the charges.

    A schedule for it covers money coming in, so it is marked scheduled: a charge of
    the same name would not be.
    """
    plan = _monthly("SAVINGS INTEREST", 500, 30, None)
    schedule = {"payee_name": "Savings Interest", "amount": 500, "deleted": False}
    assert charges.find(plan, [schedule], CATEGORIES, TODAY).charges == []
    [interest] = charges.find(plan, [schedule], CATEGORIES, TODAY, include_income=True).charges
    assert (interest.payee, interest.monthly_amount) == ("SAVINGS INTEREST", 0.5)
    assert interest.scheduled is True


def test_a_recurring_amount_of_nothing_is_neither_a_charge_nor_income() -> None:
    """A payee seen every month for 0.00 costs nothing and brings nothing: not listed."""
    plan = _monthly("ZERO CO", 0, 9, "c-subs")
    found = charges.find(plan, [], CATEGORIES, TODAY, include_income=True)
    assert found.charges == []
    assert found.yearly_total == 0.0


def test_a_schedule_of_nothing_covers_no_charge() -> None:
    """A schedule left at 0.00 is money neither in nor out: it covers no charge."""
    empty = {"payee_name": "STREAMFLIX", "amount": 0, "deleted": False}
    plan = _monthly("STREAMFLIX", -13_490, 15, "c-subs")
    [stream] = charges.find(plan, [empty], CATEGORIES, TODAY).charges
    assert stream.scheduled is False
