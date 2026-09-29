"""find_recurring_charges through the MCP protocol: read-only, three YNAB requests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from .mcp_helpers import call

RIGHT_TO_LEFT = chr(0x202E)
"""A control character a bank label can carry to reverse what is displayed."""
_MONTHS = ["2026-06", "2026-07", "2026-08"]


def _monthly(payee: str, amount: int, day: int, category: str) -> list[dict[str, Any]]:
    """The same payee, amount and category, once in each of the months."""
    return [
        {"id": f"{category}-{m}", "payee_name": payee, "amount": amount, "date": f"{m}-{day}"}
        | {"category_id": category, "deleted": False, "transfer_account_id": None}
        for m in _MONTHS
    ]


_TXS = _monthly("STREAMFLIX" + RIGHT_TO_LEFT, -13_490, 15, "c-subs") + _monthly(
    "ACME PAYROLL", 3_200_000, 28, "c-in"
)
_CATS = [{"id": "c-subs", "name": "Subscriptions"}, {"id": "c-in", "name": "Inflow"}]


@pytest.fixture(name="ynab")
def _ynab() -> Iterator[dict[str, AsyncMock]]:
    mocks = {
        "get_transactions": AsyncMock(return_value=_TXS),
        "get_scheduled_transactions": AsyncMock(return_value=[]),
        "get_categories": AsyncMock(return_value=_CATS),
    }
    with (
        patch("avenir_mcp.client.get_transactions", mocks["get_transactions"]),
        patch("avenir_mcp.client.get_scheduled_transactions", mocks["get_scheduled_transactions"]),
        patch("avenir_mcp.client.get_categories", mocks["get_categories"]),
        patch("avenir_mcp.app.today", lambda: __import__("datetime").date(2026, 9, 25)),
    ):
        yield mocks


def test_recurring_charges_come_with_their_yearly_cost(ynab: dict[str, Any]) -> None:
    """Streaming, 13.49 a month: 161.88 a year, in Subscriptions; the salary left out."""
    answer = call("find_recurring_charges", {"plan_id": "b1"}).structured_content
    assert answer["charges"] == [
        {
            "payee": "STREAMFLIX",
            "monthly_amount": -13.49,
            "yearly_amount": -161.88,
            "day": 15,
            "months_seen": 3,
            "category": "Subscriptions",
            "scheduled": False,
        }
    ]
    assert answer["yearly_total"] == -161.88
    assert answer["months_looked_at"] == ["2026-05", "2026-06", "2026-07", "2026-08"]
    assert all(mock.await_count == 1 for mock in ynab.values())


def test_income_is_listed_when_asked(ynab: dict[str, Any]) -> None:
    """With include_income, the salary follows the charges; the total stays the charges'."""
    answer = call(
        "find_recurring_charges", {"plan_id": "b1", "include_income": True}
    ).structured_content
    assert [c["payee"] for c in answer["charges"]] == ["STREAMFLIX", "ACME PAYROLL"]
    assert answer["yearly_total"] == -161.88
    assert ynab["get_transactions"].await_count == 1
