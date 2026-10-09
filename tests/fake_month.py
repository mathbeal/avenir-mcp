# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""A fake YNAB month for the budget tools: each category's budgeted and spent milliunits."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


class FakeMonth:
    """Categories of one month, and the amounts the tools set, as YNAB would hold them."""

    def __init__(self, names: dict[str, str], budgeted: dict[str, int]) -> None:
        """Start with each category's name and budgeted milliunits, nothing spent yet."""
        self.names = names
        self.budgeted = budgeted
        self.spent = dict.fromkeys(budgeted, 0)
        self.sets: list[tuple[str, str, float]] = []
        self.calls = 0
        self.failing_calls: set[int] = set()
        self.failure: Exception = RuntimeError("YNAB 500: internal error")
        """What a failing call raises: a refusal by default, a lost answer when a test says so."""

    async def get_month_categories(self, _plan_id: str, _month: str) -> list[dict[str, Any]]:
        """Categories of the month, as YNAB returns them."""
        return [
            {
                "id": cat_id,
                "name": self.names[cat_id],
                "category_group_name": "Everyday",
                "budgeted": milli,
                "activity": self.spent[cat_id],
                "balance": milli + self.spent[cat_id],
            }
            for cat_id, milli in self.budgeted.items()
        ]

    async def set_category_budgeted(
        self, _plan_id: str, month: str, category_id: str, amount: float
    ) -> dict[str, Any]:
        """Record and apply the new budgeted amount, or fail like YNAB on the calls told to."""
        self.calls += 1
        if self.calls in self.failing_calls:
            raise self.failure
        self.sets.append((month, category_id, amount))
        self.budgeted[category_id] = round(amount * 1000)
        return {"id": category_id, "budgeted": self.budgeted[category_id]}


@contextmanager
def serving(fake: FakeMonth, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Answer the budget tools' YNAB calls from the fake, with a journal in tmp_path."""
    monkeypatch.setenv("AVENIR_MCP_JOURNAL", str(tmp_path / "journal.jsonl"))
    with (
        patch("avenir_mcp.client.get_month_categories", fake.get_month_categories),
        patch("avenir_mcp.client.set_category_budgeted", fake.set_category_budgeted),
    ):
        yield
