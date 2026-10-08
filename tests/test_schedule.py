# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for schedule.py — the dates on which scheduled transactions fall."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from avenir_mcp import schedule

from .factories import scheduled

_ACCOUNTS = {"acc": "Checking", "acc-savings": "Savings"}
_CATEGORIES = {"c-rent": "Rent"}


def _sched(first: str, next_: str, frequency: str, **extra: Any) -> dict[str, Any]:
    return scheduled("s1", first, next_, frequency, **{"payee_name": "Landlord", **extra})


def _dates(
    *items: dict[str, Any], since: str = "2026-10-01", until: str = "2026-12-31"
) -> list[str]:
    found = schedule.occurrences(
        list(items), _ACCOUNTS, _CATEGORIES, date.fromisoformat(since), date.fromisoformat(until)
    )
    return [o.date for o in found]


@pytest.mark.parametrize(
    ("frequency", "expected"),
    [
        ("monthly", ["2026-10-03", "2026-11-03", "2026-12-03"]),
        ("everyOtherMonth", ["2026-10-03", "2026-12-03"]),
        ("every3Months", ["2026-10-03"]),
        ("never", ["2026-10-03"]),
        ("every4Weeks", ["2026-10-03", "2026-10-31", "2026-11-28", "2026-12-26"]),
    ],
)
def test_each_frequency_repeats_from_the_next_date(frequency: str, expected: list[str]) -> None:
    """The next date, then again at the frequency's interval, up to the end date."""
    assert _dates(_sched("2026-01-03", "2026-10-03", frequency)) == expected


def test_weekly_frequencies_count_their_days() -> None:
    """Daily, weekly and every other week step by 1, 7 and 14 days."""
    window = {"since": "2026-10-01", "until": "2026-10-15"}
    assert len(_dates(_sched("2026-01-01", "2026-10-01", "daily"), **window)) == 15
    assert _dates(_sched("2026-01-01", "2026-10-01", "weekly"), **window) == [
        "2026-10-01",
        "2026-10-08",
        "2026-10-15",
    ]
    assert _dates(_sched("2026-01-01", "2026-10-01", "everyOtherWeek"), **window) == [
        "2026-10-01",
        "2026-10-15",
    ]


def test_yearly_frequencies_keep_their_day() -> None:
    """Twice a year, yearly and every other year step by 6, 12 and 24 months."""
    window = {"since": "2026-10-01", "until": "2029-01-01"}
    assert _dates(_sched("2025-10-15", "2026-10-15", "twiceAYear"), **window)[:3] == [
        "2026-10-15",
        "2027-04-15",
        "2027-10-15",
    ]
    assert _dates(_sched("2025-10-15", "2026-10-15", "yearly"), **window) == [
        "2026-10-15",
        "2027-10-15",
        "2028-10-15",
    ]
    assert _dates(_sched("2024-10-15", "2026-10-15", "everyOtherYear"), **window) == [
        "2026-10-15",
        "2028-10-15",
    ]


def test_a_month_end_day_falls_on_the_last_day_of_shorter_months() -> None:
    """Scheduled on the 31st: the 30th in November, the 31st again in December."""
    item = _sched("2026-01-31", "2026-10-31", "monthly")
    assert _dates(item) == ["2026-10-31", "2026-11-30", "2026-12-31"]


def test_twice_a_month_falls_on_its_day_and_fifteen_days_later() -> None:
    """Twice a month: the scheduled day, and the day fifteen days after it."""
    item = _sched("2026-01-01", "2026-10-01", "twiceAMonth")
    assert _dates(item, until="2026-11-30") == [
        "2026-10-01",
        "2026-10-16",
        "2026-11-01",
        "2026-11-16",
    ]


def test_a_date_already_past_moves_on_to_the_window() -> None:
    """A next date YNAB left in the past counts from its first date inside the window."""
    assert _dates(_sched("2026-01-03", "2026-08-03", "monthly"), until="2026-10-31") == [
        "2026-10-03"
    ]


def test_deleted_and_out_of_window_schedules_are_left_out() -> None:
    """A deleted schedule, or one that starts after the end date, gives nothing.

    The deleted one comes first, before a schedule that does fall in the window: passing
    over it cannot mean stopping at it.
    """
    deleted = _sched("2026-01-03", "2026-10-03", "monthly", deleted=True)
    kept = _sched("2026-01-07", "2026-10-07", "never", id="s3")
    later = _sched("2027-01-03", "2027-01-03", "monthly", id="s2")
    assert _dates(deleted, kept, later) == ["2026-10-07"]


def test_an_occurrence_says_what_it_is_and_shows_bank_text_safely() -> None:
    """Amount in currency units, account and category names, text made safe."""
    item = _sched("2026-01-03", "2026-10-03", "never", memo="line\nbreak", payee_name="A\u202eB")
    found = schedule.occurrences(
        [item], _ACCOUNTS, _CATEGORIES, date(2026, 10, 1), date(2026, 10, 31)
    )
    assert len(found) == 1
    assert found[0].model_dump() == {
        "scheduled_id": "s1",
        "date": "2026-10-03",
        "amount": -950.0,
        "payee": "AB",
        "memo": "line break",
        "account": "Checking",
        "category": "Rent",
        "frequency": "never",
        "transfer": False,
    }


def test_a_transfer_and_a_split_say_so() -> None:
    """A transfer names no category; a split one is marked Split."""
    transfer = _sched(
        "2026-01-29", "2026-10-29", "never", category_id=None, transfer_account_id="acc-savings"
    )
    split = _sched(
        "2026-01-05",
        "2026-10-05",
        "never",
        id="s2",
        category_id=None,
        subtransactions=[{"id": "x", "category_id": "c-rent", "deleted": False}],
    )
    found = schedule.occurrences(
        [transfer, split], _ACCOUNTS, _CATEGORIES, date(2026, 10, 1), date(2026, 10, 31)
    )
    assert [(o.category, o.transfer) for o in found] == [("Split", False), (None, True)]


def test_occurrences_come_in_date_order() -> None:
    """Earliest first, whatever the order YNAB listed the schedules in."""
    late = _sched("2026-01-20", "2026-10-20", "never", id="late")
    early = _sched("2026-01-02", "2026-10-02", "never", id="early")
    assert _dates(late, early) == ["2026-10-02", "2026-10-20"]


# ---------------------------------------------------------------------------
# Cases found by mutation testing
# ---------------------------------------------------------------------------


def test_dates_before_the_window_are_passed_over_not_stopped_at() -> None:
    """A schedule whose next dates are still in the past keeps the ones inside the window."""
    weekly = _sched("2026-01-01", "2026-09-17", "weekly")
    assert _dates(weekly, until="2026-10-15") == ["2026-10-01", "2026-10-08", "2026-10-15"]


def test_a_split_whose_every_part_is_deleted_is_not_a_split() -> None:
    """Deleted subtransactions are gone: the schedule's own category is the one shown."""
    item = _sched(
        "2026-01-05",
        "2026-10-05",
        "never",
        subtransactions=[
            {"id": "x", "category_id": "c-rent", "deleted": True},
            {"id": "y", "category_id": "c-rent", "deleted": True},
        ],
    )
    found = schedule.occurrences(
        [item], _ACCOUNTS, _CATEGORIES, date(2026, 10, 1), date(2026, 10, 31)
    )
    assert [o.category for o in found] == ["Rent"]


def test_a_schedule_with_no_note_has_none() -> None:
    """No memo reads as null, not as an empty note."""
    found = schedule.occurrences(
        [_sched("2026-01-03", "2026-10-03", "never")],
        _ACCOUNTS,
        _CATEGORIES,
        date(2026, 10, 1),
        date(2026, 10, 31),
    )
    assert [o.memo for o in found] == [None]


def test_an_account_the_plan_no_longer_names_shows_as_an_empty_name() -> None:
    """A schedule on an account the plan does not list still comes back, without a name."""
    found = schedule.occurrences(
        [_sched("2026-01-03", "2026-10-03", "never", account_id="gone")],
        _ACCOUNTS,
        _CATEGORIES,
        date(2026, 10, 1),
        date(2026, 10, 31),
    )
    assert [o.account for o in found] == [""]
