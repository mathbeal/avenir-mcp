# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Invented YNAB objects for tests, with every field YNAB sends."""

from __future__ import annotations

from typing import Any


def scheduled(
    sched_id: str, first: str, next_: str, frequency: str, **extra: Any
) -> dict[str, Any]:
    """A scheduled transaction as YNAB returns it: rent of 950.00 on Checking by default.

    Args:
        sched_id: Its id, also its payee's name.
        first: The first date it was scheduled on.
        next_: Its next date.
        frequency: YNAB's frequency, e.g. "monthly".
        **extra: Fields to change, e.g. amount or transfer_account_id.

    Returns:
        The scheduled transaction.
    """
    item: dict[str, Any] = {
        "id": sched_id,
        "date_first": first,
        "date_next": next_,
        "frequency": frequency,
        "amount": -950_000,
        "memo": None,
        "account_id": "acc",
        "payee_name": sched_id,
        "category_id": "c-rent",
        "transfer_account_id": None,
        "subtransactions": [],
        "deleted": False,
    }
    item.update(extra)
    return item
