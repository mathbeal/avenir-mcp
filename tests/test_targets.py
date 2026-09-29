"""Tests for targets.py: describing a category's target, and what brings it back."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import targets, triage


def _cat(**goal: Any) -> dict[str, Any]:
    base = {"id": "c1", "name": "Holidays", "goal_type": None, "goal_target": None}
    return base | goal


NEED_MONTHLY = _cat(
    goal_type="NEED",
    goal_target=50_000,
    goal_cadence=1,
    goal_cadence_frequency=1,
    goal_needs_whole_amount=True,
)
NEED_BY_DATE = _cat(
    goal_type="NEED",
    goal_target=1_200_000,
    goal_target_date="2027-06-01",
    goal_cadence=0,
    goal_needs_whole_amount=False,
)
MONTHLY_FUNDING = _cat(goal_type="MF", goal_target=30_000)
CARD = _cat(name="Visa", category_group_name=triage.CARD_GROUP)
LOAN = _cat(name="Car loan", goal_type="DEBT", goal_target=250_000)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (_cat(), "no target"),
        (NEED_MONTHLY, "50.00 each month"),
        (NEED_BY_DATE, "1200.00 by 2027-06-01"),
        (
            _cat(goal_type="NEED", goal_target=90_000, goal_cadence=2, goal_cadence_frequency=1),
            "90.00 each week",
        ),
        (
            _cat(goal_type="NEED", goal_target=90_000, goal_cadence=13, goal_cadence_frequency=1),
            "90.00 each year",
        ),
        (MONTHLY_FUNDING, "30.00 (monthly funding)"),
        (_cat(goal_type="TB", goal_target=500_000), "500.00 (target balance)"),
        (_cat(goal_type="DEBT", goal_target=100_000), "100.00 (debt payment)"),
    ],
)
def test_a_target_is_described_as_the_user_reads_it(
    category: dict[str, Any], expected: str
) -> None:
    """Amount, rhythm or date; the YNAB kind when the API cannot set it."""
    assert targets.describe(category) == expected


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (_cat(), {"goal_target": None}),
        (
            NEED_MONTHLY,
            {"goal_target": 50_000, "goal_frequency": "monthly", "goal_needs_whole_amount": True},
        ),
        (
            NEED_BY_DATE,
            {
                "goal_target": 1_200_000,
                "goal_target_date": "2027-06-01",
                "goal_needs_whole_amount": False,
            },
        ),
        (MONTHLY_FUNDING, None),
        (
            _cat(goal_type="NEED", goal_target=90_000, goal_cadence=1, goal_cadence_frequency=2),
            None,
        ),
    ],
)
def test_what_recreates_a_target_is_known_or_none(
    category: dict[str, Any], expected: dict[str, Any] | None
) -> None:
    """A target the API can set again gives the fields that do; any other gives None."""
    assert targets.recreate(category) == expected


def test_changing_only_the_amount_keeps_any_kind_and_is_undone_exactly() -> None:
    """YNAB keeps an existing target's kind when only the amount changes: undo sets it back."""
    change = targets.plan(MONTHLY_FUNDING, amount=45.0, date=None, frequency=None)
    assert change.fields == {"goal_target": 45_000}
    assert change.undo == {"goal_target": 30_000}
    assert change.after == "45.00 (monthly funding)"


def test_a_new_rhythm_on_a_kind_the_api_cannot_set_cannot_be_undone() -> None:
    """Monthly funding replaced by a weekly target: the preview says undo cannot restore it."""
    change = targets.plan(MONTHLY_FUNDING, amount=20.0, date=None, frequency="weekly")
    assert change.fields == {"goal_target": 20_000, "goal_frequency": "weekly"}
    assert change.undo is None
    assert change.after == "20.00 each week"


def test_a_target_by_a_date_and_its_removal() -> None:
    """A date sets a one-off target; no amount removes the target, undone by recreating it."""
    change = targets.plan(_cat(), amount=1200.0, date="2027-06-01", frequency=None)
    assert change.fields == {"goal_target": 1_200_000, "goal_target_date": "2027-06-01"}
    assert change.undo == {"goal_target": None}
    removal = targets.plan(NEED_MONTHLY, amount=None, date=None, frequency=None)
    assert removal.fields == {"goal_target": None}
    assert removal.after == "no target"
    assert removal.undo == targets.recreate(NEED_MONTHLY)


def test_an_amount_alone_on_a_category_without_target_is_monthly() -> None:
    """With no target yet and no rhythm given, YNAB sets a monthly one; undo removes it."""
    change = targets.plan(_cat(), amount=40.0, date=None, frequency=None)
    assert change.fields == {"goal_target": 40_000}
    assert change.after == "40.00 each month"
    assert change.undo == {"goal_target": None}


@pytest.mark.parametrize(
    ("amount", "date", "frequency", "expected"),
    [
        (100.0, "2027-01-01", "monthly", "either a date or a frequency"),
        (0.0, None, None, "greater than 0"),
        (-5.0, None, "monthly", "greater than 0"),
        (None, "2027-01-01", None, "no date"),
        (None, None, "monthly", "no date"),
    ],
)
def test_contradictory_targets_are_refused(
    amount: float | None, date: str | None, frequency: str | None, expected: str
) -> None:
    """YNAB refuses a date with a frequency; a removal takes neither; amounts are positive."""
    with pytest.raises(ValueError, match=expected):
        targets.plan(_cat(), amount=amount, date=date, frequency=frequency)


def test_an_amount_alone_on_a_card_category_is_monthly_funding() -> None:
    """YNAB gives a credit card payment category monthly funding, and the preview says so."""
    change = targets.plan(CARD, amount=150.0, date=None, frequency=None)
    assert change.fields == {"goal_target": 150_000}
    assert change.after == "150.00 (monthly funding)"
    assert change.undo == {"goal_target": None}


def test_a_new_amount_on_a_loan_category_keeps_its_debt_payment() -> None:
    """Only the amount changes: the debt payment stays, and undo sets the amount back."""
    change = targets.plan(LOAN, amount=300.0, date=None, frequency=None)
    assert change.after == "300.00 (debt payment)"
    assert change.undo == {"goal_target": 250_000}


@pytest.mark.parametrize(
    ("category", "date", "frequency", "expected"),
    [
        (CARD, None, "monthly", "no frequency on a credit card payment category"),
        (LOAN, None, "weekly", "neither a date nor a frequency on a category paired"),
        (LOAN, "2027-01-01", None, "neither a date nor a frequency on a category paired"),
    ],
)
def test_what_card_and_loan_categories_do_not_take_is_refused_first(
    category: dict[str, Any], date: str | None, frequency: str | None, expected: str
) -> None:
    """YNAB refuses these after the user confirms; they are refused before asking."""
    with pytest.raises(ValueError, match=expected):
        targets.plan(category, amount=100.0, date=date, frequency=frequency)


def test_a_date_on_a_card_category_is_allowed() -> None:
    """YNAB lists no limit on a date for a credit card payment category: it is sent."""
    change = targets.plan(CARD, amount=900.0, date="2027-03-01", frequency=None)
    assert change.fields == {"goal_target": 900_000, "goal_target_date": "2027-03-01"}


def test_nothing_to_change_is_said() -> None:
    """The same target again is no change."""
    change = targets.plan(NEED_MONTHLY, amount=50.0, date=None, frequency="monthly")
    assert change.unchanged
