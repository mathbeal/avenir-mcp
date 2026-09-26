"""list_scheduled_transactions through the MCP protocol: what falls due, and when."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from .factories import scheduled
from .mcp_helpers import call

_ACCOUNTS = [{"id": "acc", "name": "Checking"}, {"id": "acc-savings", "name": "Savings"}]
_CATS = [{"id": "c-rent", "name": "Rent"}]


def _sched(
    sched_id: str, next_: str, amount: int, frequency: str = "monthly", **extra: Any
) -> dict[str, Any]:
    return scheduled(sched_id, next_, next_, frequency, amount=amount, **extra)


_SCHEDULED = [
    _sched("rent", "2026-10-03", -950_000),
    _sched("salary", "2026-09-28", 3_200_000, category_id=None),
    _sched(
        "to-savings", "2026-09-29", -200_000, category_id=None, transfer_account_id="acc-savings"
    ),
    _sched("savings-fee", "2026-10-10", -2_000, account_id="acc-savings", frequency="never"),
]


@pytest.fixture(name="read")
def _read() -> Iterator[AsyncMock]:
    """A fake YNAB on 26 September 2026; the mock it yields records the reads."""
    schedules = AsyncMock(return_value=_SCHEDULED)
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.get_scheduled_transactions", schedules),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 26)),
    ):
        yield schedules


def test_the_next_thirty_days_by_default(read: AsyncMock) -> None:
    """From today to 30 days later, earliest first, in one read of the schedules."""
    found = call("list_scheduled_transactions", {"plan_id": "b1"}).structured_content
    assert [(o["date"], o["scheduled_id"]) for o in found["occurrences"]] == [
        ("2026-09-28", "salary"),
        ("2026-09-29", "to-savings"),
        ("2026-10-03", "rent"),
        ("2026-10-10", "savings-fee"),
    ]
    read.assert_awaited_once_with("b1")


def test_totals_leave_transfers_between_accounts_out(read: AsyncMock) -> None:
    """Money in and out of the plan, not money moved from one account to another."""
    args = {"plan_id": "b1", "since_date": "2026-10-01", "until_date": "2026-10-15"}
    found = call("list_scheduled_transactions", args).structured_content
    assert (found["inflows"], found["outflows"]) == (0.0, -952.0)
    assert read.await_count == 1


@pytest.mark.usefixtures("read")
def test_accounts_narrow_the_list() -> None:
    """Only the accounts asked for."""
    args = {"plan_id": "b1", "since_date": "2026-10-01", "account_ids": ["acc-savings"]}
    found = call("list_scheduled_transactions", args).structured_content
    assert [o["scheduled_id"] for o in found["occurrences"]] == ["savings-fee"]


def test_a_bad_window_is_refused_before_any_request(read: AsyncMock) -> None:
    """Reversed dates, too long a window or an unknown account: nothing is read."""
    for args in (
        {"since_date": "2026-10-10", "until_date": "2026-10-01"},
        {"since_date": "2026-10-01", "until_date": "2028-10-01"},
        {"account_ids": ["nope"]},
    ):
        result = call("list_scheduled_transactions", {"plan_id": "b1", **args})
        assert result.is_error
    read.assert_not_awaited()
