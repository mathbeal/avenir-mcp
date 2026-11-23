# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for pace.py — keeping avenir-mcp within YNAB's rolling-hour request limit."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from avenir_mcp import pace

# ---------------------------------------------------------------------------
# __init__ and reset
# ---------------------------------------------------------------------------


def test_a_new_pace_starts_with_nothing_sent_and_no_pause() -> None:
    """A fresh Pace has sent nothing and is not paused."""
    clock = pace.Pace()
    assert not clock.sent
    assert clock.paused_until == 0.0


def test_reset_forgets_what_was_sent_and_any_pause() -> None:
    """reset() clears both the sent requests and a pause, as a fresh Pace would be."""
    clock = pace.Pace()
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        clock.take()
        clock.refused()

    clock.reset()

    assert not clock.sent
    assert clock.paused_until == 0.0


# ---------------------------------------------------------------------------
# take: refusing or counting a request
# ---------------------------------------------------------------------------


def test_take_counts_a_request_sent_now() -> None:
    """An allowed request is timestamped with the clock's current reading."""
    clock = pace.Pace()
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        clock.take()
    assert list(clock.sent) == [1000.0]


def test_take_refuses_while_paused() -> None:
    """A request made before a pause ends is refused, and never counted as sent."""
    clock = pace.Pace()
    clock.paused_until = 1120.0
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        with pytest.raises(RuntimeError) as raised:
            clock.take()
    assert str(raised.value) == (
        "YNAB's limit of 200 requests per hour was reached. Nothing was sent: "
        "avenir-mcp calls YNAB again in 2 minutes. Tell the user; do not retry before then."
    )
    assert not clock.sent


def test_take_allows_a_request_exactly_when_the_pause_ends() -> None:
    """The pause ends at paused_until itself: a request made then is allowed through."""
    clock = pace.Pace()
    clock.paused_until = 1000.0
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        clock.take()
    assert list(clock.sent) == [1000.0]


def test_take_drops_requests_older_than_the_rolling_hour() -> None:
    """A request sent exactly one hour ago no longer counts against the budget."""
    clock = pace.Pace()
    clock.sent.extend([0.0, 10.0])
    with patch("avenir_mcp.pace.time.monotonic", return_value=3600.0):
        clock.take()
    assert list(clock.sent) == [10.0, 3600.0]


def test_take_refuses_once_the_hour_s_budget_is_spent() -> None:
    """At 180 requests already counted in the hour, a 181st is refused."""
    clock = pace.Pace()
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        clock.sent.extend([400.0, *([1000.0] * 179)])
        with pytest.raises(RuntimeError) as raised:
            clock.take()
    assert str(raised.value) == (
        "avenir-mcp sent 180 requests to YNAB in the last hour, close to YNAB's limit of "
        "200 per hour. Nothing was sent: the next request can leave in 50 minutes. Tell "
        "the user; do not retry before then."
    )
    assert len(clock.sent) == 180


# ---------------------------------------------------------------------------
# refused: how long to pause after a 429
# ---------------------------------------------------------------------------


def test_refused_without_a_retry_after_pauses_for_ten_minutes() -> None:
    """YNAB named no delay of its own: the default pause of 600 seconds applies."""
    clock = pace.Pace()
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        held = clock.refused()
    assert held == 600.0
    assert clock.paused_until == 1600.0


def test_refused_with_a_retry_after_pauses_for_exactly_that_long() -> None:
    """A Retry-After of its own overrides avenir-mcp's default pause."""
    clock = pace.Pace()
    with patch("avenir_mcp.pace.time.monotonic", return_value=1000.0):
        held = clock.refused(30.0)
    assert held == 30.0
    assert clock.paused_until == 1030.0


# ---------------------------------------------------------------------------
# _minutes: rounding a wait up to whole minutes
# ---------------------------------------------------------------------------


def test_minutes_rounds_up_to_the_next_whole_minute() -> None:
    """61 seconds is already into a second minute, so it rounds up to 2."""
    assert pace._minutes(61) == "2 minutes"  # pylint: disable=protected-access


def test_minutes_is_singular_at_one_minute_or_less() -> None:
    """A wait of a minute or less is still said as a whole minute, singular."""
    assert pace._minutes(60) == "1 minute"  # pylint: disable=protected-access
