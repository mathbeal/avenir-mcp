# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for age.py: YNAB's Age of Money, month by month."""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp import age

TODAY = date(2026, 9, 25)


def _month(month: str, days: int | None, deleted: bool = False) -> dict[str, Any]:
    """A month summary as client.get_months gives it."""
    return {
        "month": f"2026-{month}-01",
        "income": 0,
        "budgeted": 0,
        "activity": 0,
        "to_be_budgeted": 0,
        "age_of_money": days,
        "note": None,
        "deleted": deleted,
    }


def _summary(months: list[dict[str, Any]], count: int = 12, today: date = TODAY) -> Any:
    return age.summary(months, today, count)


def test_each_month_has_its_figure_and_the_change_from_the_month_before() -> None:
    """17, 48, 47 days: up 31, then down 1."""
    answer = _summary([_month("07", 17), _month("08", 48), _month("09", 47)])
    assert [(m.month, m.days, m.change) for m in answer.months] == [
        ("2026-07", 17, None),
        ("2026-08", 48, 31),
        ("2026-09", 47, -1),
    ]
    assert (answer.days, answer.as_of) == (47, "2026-09")
    assert (answer.change, answer.trend) == (30, "up")


def test_the_message_says_what_the_figure_means() -> None:
    """Over 30 days: living on last month's income; the change since the first month."""
    message = _summary([_month("07", 17), _month("08", 48), _month("09", 47)]).message
    assert "47 days old" in message
    assert "last month's income" in message
    assert "up by 30 days since 2026-07" in message


def test_under_thirty_days_the_money_is_spent_within_the_month() -> None:
    """21 days, down from 25: spent within the month it came in."""
    answer = _summary([_month("08", 25), _month("09", 21)])
    assert (answer.change, answer.trend) == (-4, "down")
    assert "within a month" in answer.message
    assert "down by 4 days since 2026-08" in answer.message


def test_a_steady_figure_is_said_to_be_steady() -> None:
    """The same figure at both ends."""
    answer = _summary([_month("07", 30), _month("08", 35), _month("09", 30)])
    assert (answer.change, answer.trend) == (0, "steady")
    assert "unchanged since 2026-07" in answer.message


def test_future_and_deleted_months_are_left_out_and_the_last_ones_kept() -> None:
    """YNAB lists months budgeted ahead: they have no Age of Money of their own yet."""
    months = [
        _month("05", 10),
        _month("06", 12, deleted=True),
        _month("07", 14),
        _month("08", 16),
        _month("09", 18),
        _month("10", 18),
        _month("11", None),
    ]
    answer = _summary(list(reversed(months)), count=3)
    assert [m.month for m in answer.months] == ["2026-07", "2026-08", "2026-09"]
    assert (answer.days, answer.change) == (18, 4)
    wider = _summary(list(reversed(months)), count=4)
    assert [m.month for m in wider.months] == ["2026-05", "2026-07", "2026-08", "2026-09"]


def test_months_without_a_figure_are_named() -> None:
    """A new plan: YNAB had no figure for June, then one from July."""
    answer = _summary([_month("06", None), _month("07", 17), _month("08", 48)])
    assert [m.change for m in answer.months] == [None, None, 31]
    assert (answer.change, answer.as_of) == (31, "2026-08")
    assert any("2026-06" in note and "enough history" in note for note in answer.notes)


def test_without_any_figure_the_answer_says_why() -> None:
    """YNAB returns null everywhere until the plan has enough history."""
    answer = _summary([_month("08", None), _month("09", None)])
    assert (answer.days, answer.as_of, answer.change, answer.trend) == (None, None, None, None)
    assert "enough history" in answer.message


def test_a_single_figure_has_no_trend() -> None:
    """One month known: its figure, no change."""
    answer = _summary([_month("09", 40)])
    assert (answer.days, answer.change, answer.trend) == (40, None, None)
    assert "since" not in answer.message


def test_without_any_month_nothing_is_given() -> None:
    """An empty answer from YNAB."""
    answer = _summary([])
    assert answer.months == []
    assert answer.days is None
    assert "no month" in answer.message


def test_fewer_months_than_asked_are_noted() -> None:
    """Twelve asked, three held."""
    answer = _summary([_month("07", 17), _month("08", 48), _month("09", 47)])
    assert any("only 3 months" in note for note in answer.notes)
    assert not any(
        "only" in note for note in _summary([_month("08", 48), _month("09", 47)], count=2).notes
    )


def test_a_missing_current_month_is_noted() -> None:
    """In October, YNAB's latest month is September: its figure is the latest."""
    answer = _summary([_month("08", 48), _month("09", 47)], today=date(2026, 10, 2))
    assert answer.as_of == "2026-09"
    assert any("2026-10" in note for note in answer.notes)
    assert not any("2026-10" in note for note in _summary([_month("09", 47)]).notes)


def test_every_answer_states_how_ynab_counts() -> None:
    """The rule and the current month's volatility, in plain words."""
    notes = " ".join(_summary([_month("09", 47)]).notes)
    assert "oldest money" in notes
    assert "current month" in notes


# ---------------------------------------------------------------------------
# Cases found by mutation testing
# ---------------------------------------------------------------------------

_HOW_YNAB_COUNTS = (
    "Age of Money is YNAB's own figure: for the latest payments out of the budget "
    "accounts, how many days passed since that money came in, the oldest money spent "
    "first, averaged."
)
_THE_CURRENT_MONTH_MOVES = (
    "The current month's figure moves with each payment; a past month's is the one YNAB "
    "keeps for it."
)


def test_every_answer_opens_with_the_same_two_notes_and_nothing_else() -> None:
    """A full set of months up to this one has nothing missing to report."""
    answer = _summary([_month("08", 48), _month("09", 47)], count=2)
    assert answer.notes == [_HOW_YNAB_COUNTS, _THE_CURRENT_MONTH_MOVES]


def test_the_months_without_a_figure_are_listed_together() -> None:
    """Two months with no figure are named in one note, in order."""
    answer = _summary([_month("06", None), _month("07", None), _month("08", 17)], count=3)
    assert answer.notes[2:] == [
        "No figure for 2026-06, 2026-07: YNAB did not have enough history of money in and out yet.",
        "YNAB has no month 2026-09 yet: the latest is 2026-08.",
    ]


def test_the_note_about_a_missing_current_month_names_the_latest_one() -> None:
    """The latest month YNAB holds, not the one before it."""
    answer = _summary([_month("07", 40), _month("08", 48)], count=2)
    assert answer.notes[2] == "YNAB has no month 2026-09 yet: the latest is 2026-08."


def test_exactly_thirty_days_is_already_the_buffer() -> None:
    """Thirty days is the goal reached, not the last day short of it."""
    answer = _summary([_month("09", age.A_MONTH)])
    assert answer.message == (
        "Your money is 30 days old (2026-09, YNAB's Age of Money): what you spend came "
        "in 30 days before, on average. Over 30 days: you are living on last month's "
        "income, the buffer YNAB aims for."
    )


def test_under_the_buffer_the_message_says_what_a_bigger_one_buys() -> None:
    """The whole sentence an agent relays, not a fragment of it."""
    answer = _summary([_month("08", 25), _month("09", 21)], count=2)
    assert answer.message == (
        "Your money is 21 days old (2026-09, YNAB's Age of Money): what you spend came "
        "in 21 days before, on average. Under 30 days: money is spent within a month of "
        "coming in; the older it gets, the bigger the buffer between pay and bills. "
        "It went down by 4 days since 2026-08."
    )


def test_a_gain_of_one_day_is_a_trend_upwards() -> None:
    """One day more is already up, not steady."""
    answer = _summary([_month("08", 20), _month("09", 21)], count=2)
    assert (answer.change, answer.trend) == (1, "up")


def test_with_no_month_at_all_the_message_names_the_month_asked_about() -> None:
    """The user is told which month YNAB was asked up to."""
    assert _summary([]).message == (
        "YNAB returned no month up to 2026-09: no Age of Money to give."
    )


def test_with_no_figure_at_all_the_message_says_what_ynab_waits_for() -> None:
    """Null everywhere: the whole sentence, so the agent can relay the reason."""
    assert _summary([_month("08", None), _month("09", None)], count=2).message == (
        "YNAB gives no Age of Money for the last 2 months: it shows one once the plan "
        "has enough history of money in and out."
    )
