# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for underfunded.py: the targets short this month, the most urgent first."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import underfunded

from .mcp_helpers import FLAT, FORGED


def _cat(  # pylint: disable=too-many-arguments
    key: str,
    kind: str | None,
    *,
    target: int = 100_000,
    needed: int = 0,
    left: int | None = None,
    due: str | None = None,
    cadence: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """A category of a month as YNAB returns it, named after its id, amounts in milliunits."""
    goal = (
        {}
        if kind is None
        else {
            "goal_type": kind,
            "goal_target": target,
            "goal_target_date": due,
            "goal_cadence": cadence,
            "goal_cadence_frequency": 1,
            "goal_under_funded": needed,
            "goal_overall_left": needed if left is None else left,
            "goal_percentage_complete": 40,
            "goal_months_to_budget": 3 if due else None,
            "goal_snoozed_at": None,
        }
    )
    return (
        {
            "id": key,
            "name": key.title(),
            "category_group_name": "Bills",
            "hidden": False,
            "deleted": False,
        }
        | goal
        | extra
    )


def _month(categories: list[dict[str, Any]], ready: int = 1_000_000) -> dict[str, Any]:
    """A month as YNAB returns it."""
    return {"month": "2026-09-01", "to_be_budgeted": ready, "categories": categories}


MIXED = [
    _cat("rent", "NEED", target=950_000, cadence=1),
    _cat("groceries", "NEED", target=450_000, needed=50_000, cadence=1),
    _cat("phone", "MF", target=20_000, needed=20_000),
    _cat("tennis", "NEED", target=480_000, needed=40_000, left=400_000, due="2026-12-01"),
    _cat("rail", "NEED", target=250_000, needed=35_000, left=160_000, due="2026-10-01"),
    _cat("cushion", "TB", target=2_000_000, needed=300_000, left=300_000),
    _cat("car", "TB", target=900_000, needed=90_000, left=90_000),
    _cat("insurance", "NEED", target=420_000, needed=70_000, due="2026-10-20", cadence=13),
    _cat("loan", "DEBT", target=400_000, needed=400_000),
    _cat("restaurants", None),
]


def test_most_urgent_first() -> None:
    """Dated targets soonest first, then monthly ones largest first, then the rest."""
    answer = underfunded.summary(_month(MIXED), None)
    assert [(t.category_id, t.urgency) for t in answer.targets] == [
        ("rail", "due_date"),
        ("insurance", "due_date"),
        ("tennis", "due_date"),
        ("loan", "repeating"),
        ("groceries", "repeating"),
        ("phone", "repeating"),
        ("cushion", "other"),
        ("car", "other"),
    ]
    assert answer.on_track == 1
    assert answer.more == 0


def test_each_target_says_what_it_still_needs() -> None:
    """Needed this month, left overall, the target in words, its date and progress."""
    answer = underfunded.summary(_month(MIXED), None)
    rail = answer.targets[0]
    assert rail.model_dump() == {
        "category_id": "rail",
        "name": "Rail",
        "group": "Bills",
        "target": "250.00 by 2026-10-01",
        "due": "2026-10-01",
        "needed": 35.0,
        "left": 160.0,
        "percent_complete": 40,
        "months_left": 3,
        "urgency": "due_date",
    }
    groceries = next(t for t in answer.targets if t.category_id == "groceries")
    assert (groceries.target, groceries.due, groceries.months_left) == (
        "450.00 each month",
        None,
        None,
    )
    assert next(t for t in answer.targets if t.category_id == "loan").target == (
        "400.00 (debt payment)"
    )


def test_enough_ready_to_assign_covers_them_all() -> None:
    """1,005 needed, 1,500 to assign: enough, 495 left over."""
    answer = underfunded.summary(_month(MIXED, ready=1_500_000), None)
    assert (answer.needed, answer.ready_to_assign) == (1_005.0, 1_500.0)
    assert (answer.enough, answer.covered, answer.short_by) == (True, 1_005.0, 0.0)
    assert answer.message == (
        "8 targets need 1005.00 in 2026-09; Ready to Assign holds 1500.00: enough for all "
        "of them, with 495.00 left."
    )


def test_not_enough_says_what_it_covers_and_the_gap() -> None:
    """1,005 needed, 600 to assign: 600 of 1,005 covered, 405 short."""
    answer = underfunded.summary(_month(MIXED, ready=600_000), None)
    assert (answer.enough, answer.covered, answer.short_by) == (False, 600.0, 405.0)
    assert answer.message == (
        "8 targets need 1005.00 in 2026-09; Ready to Assign holds 600.00: it covers 600.00 "
        "of the 1005.00, 405.00 short."
    )


def test_ready_to_assign_below_zero_covers_nothing() -> None:
    """More assigned than received: nothing to cover the targets with."""
    answer = underfunded.summary(_month(MIXED[:2], ready=-20_000), None)
    assert (answer.ready_to_assign, answer.covered, answer.short_by) == (-20.0, 0.0, 50.0)
    assert "covers 0.00 of the 50.00" in answer.message


def test_a_limit_lists_the_most_urgent_and_counts_the_rest() -> None:
    """Totals count every target; the list stops at the limit."""
    answer = underfunded.summary(_month(MIXED), 2)
    assert [t.category_id for t in answer.targets] == ["rail", "insurance"]
    assert (answer.more, answer.needed) == (6, 1_005.0)
    assert any("6 more" in note for note in answer.notes)


def test_every_target_funded() -> None:
    """Nothing needed: the message says so, and every target is on track."""
    answer = underfunded.summary(_month([_cat("rent", "NEED", cadence=1)]), None)
    assert (answer.targets, answer.needed, answer.on_track, answer.enough) == ([], 0.0, 1, True)
    assert answer.message == "The 1 target of 2026-09 is funded: nothing more is needed this month."


def test_no_target_at_all() -> None:
    """A plan without targets: nothing to fund, and the message says where they are set."""
    answer = underfunded.summary(_month([_cat("rent", None)]), None)
    assert answer.targets == []
    assert answer.message == "No visible category has a target in 2026-09."


@pytest.mark.parametrize("hidden", [{"hidden": True}, {"deleted": True}])
def test_hidden_and_deleted_categories_are_left_out(hidden: dict[str, Any]) -> None:
    """Only the categories the user sees count."""
    answer = underfunded.summary(_month([_cat("old", "MF", needed=10_000, **hidden)]), None)
    assert (answer.targets, answer.on_track, answer.needed) == ([], 0, 0.0)


def test_a_snoozed_target_is_left_out_and_named() -> None:
    """A target snoozed in YNAB asks for nothing this month; a note names it."""
    snoozed = _cat("gifts", "NEED", needed=60_000, cadence=1, goal_snoozed_at="2026-09-02T10:00Z")
    answer = underfunded.summary(_month([snoozed]), None)
    assert (answer.targets, answer.needed) == ([], 0.0)
    assert any("Gifts" in note and "snoozed" in note for note in answer.notes)


def test_missing_figures_count_as_nothing() -> None:
    """YNAB may give a target without its computed figures: it needs nothing then."""
    bare = {"id": "x", "name": "X", "goal_type": "TB", "goal_target": 5_000}
    answer = underfunded.summary({"month": "2026-09-01", "categories": [bare]}, None)
    assert (answer.targets, answer.on_track, answer.ready_to_assign) == ([], 1, 0.0)


def test_names_are_shown_on_one_line() -> None:
    """A category or group name is the user's text: a line break cannot add a line."""
    forged = _cat("rent", "MF", needed=10_000, name=FORGED, category_group_name=FORGED)
    target = underfunded.summary(_month([forged]), None).targets[0]
    assert (target.name, target.group) == (FLAT, FLAT)
