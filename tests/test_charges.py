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
