# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

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
        (
            100.0,
            "2027-01-01",
            "monthly",
            "Give either a date or a frequency, not both: YNAB refuses the two.",
        ),
        (
            0.0,
            None,
            None,
            "The amount must be greater than 0; to remove the target, give none.",
        ),
        (
            -5.0,
            None,
            "monthly",
            "The amount must be greater than 0; to remove the target, give none.",
        ),
        (
            None,
            "2027-01-01",
            None,
            "To remove the target, give no amount, no date and no frequency.",
        ),
        (
            None,
            None,
            "monthly",
            "To remove the target, give no amount, no date and no frequency.",
        ),
    ],
    ids=["both", "zero", "negative", "removal with a date", "removal with a frequency"],
)
def test_contradictory_targets_are_refused(
    amount: float | None, date: str | None, frequency: str | None, expected: str
) -> None:
    """YNAB refuses a date with a frequency; a removal takes neither; amounts are positive.

    Each message is checked whole: it is what the agent reads to fix the call.
    """
    with pytest.raises(ValueError) as refusal:
        targets.plan(_cat(), amount=amount, date=date, frequency=frequency)
    assert str(refusal.value) == expected


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


# ---------------------------------------------------------------------------
# Cases found by mutation testing
# ---------------------------------------------------------------------------


def test_a_target_of_one_unit_is_allowed() -> None:
    """Greater than zero means one is enough, not that one is refused too."""
    change = targets.plan(_cat(), amount=1.0, date=None, frequency=None)
    assert change.fields == {"goal_target": 1_000}


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (_cat(goal_type="NEED", goal_target=50_000), "50.00 (spending target)"),
        (_cat(goal_type="NEED", goal_target=50_000, goal_cadence=0), "50.00 (spending target)"),
        (
            _cat(goal_type="NEED", goal_target=50_000, goal_cadence=3, goal_cadence_frequency=1),
            "50.00 (spending target)",
        ),
        (_cat(goal_type="WHAT", goal_target=50_000), "50.00 (WHAT)"),
        (_cat(goal_type="NEED"), "no target"),
        (_cat(goal_target=50_000), "no target"),
    ],
    ids=[
        "no cadence",
        "cadence 0",
        "cadence YNAB alone sets",
        "unknown kind",
        "no amount",
        "no kind",
    ],
)
def test_a_target_the_api_cannot_set_again_is_described_by_its_kind(
    category: dict[str, Any], expected: str
) -> None:
    """No rhythm the API can set: the YNAB kind is shown, by its own id when unknown.

    Half a target, which YNAB should not return, reads as no target rather than failing.
    """
    assert targets.describe(category) == expected


@pytest.mark.parametrize(
    "category",
    [_cat(goal_type="NEED"), _cat(goal_target=50_000)],
    ids=["no amount", "no kind"],
)
def test_half_a_target_is_recreated_as_no_target(category: dict[str, Any]) -> None:
    """A category YNAB returns with only one of the two fields is treated as having none."""
    assert targets.recreate(category) == {"goal_target": None}


def test_an_amount_alone_over_half_a_target_sets_a_monthly_one() -> None:
    """Both fields make a target: with only one, there is no kind to keep."""
    change = targets.plan(_cat(goal_type="NEED"), amount=40.0, date=None, frequency=None)
    assert change.after == "40.00 each month"
    assert change.undo == {"goal_target": None}


def test_the_preview_of_a_target_by_a_date_says_the_date() -> None:
    """What the user confirms is the date asked for, not the rhythm of a monthly target."""
    change = targets.plan(_cat(), amount=1200.0, date="2027-06-01", frequency=None)
    assert change.after == "1200.00 by 2027-06-01"
