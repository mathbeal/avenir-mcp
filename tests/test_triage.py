"""Tests for triage.py — one pass over the budget to prepare classification."""

from __future__ import annotations

import base64
from typing import Any

from avenir_mcp import triage

_CATEGORIES: list[dict[str, Any]] = [
    {"id": "c-food", "name": "Groceries", "category_group_name": "Everyday", "deleted": False},
    {"id": "c-fun", "name": "Leisure", "category_group_name": "Everyday", "deleted": False},
    {"id": "c-old", "name": "Old", "category_group_name": "Everyday", "deleted": True},
]


def _tx(tx_id: str, payee: str, category_id: str | None = None, **extra: Any) -> dict[str, Any]:
    tx: dict[str, Any] = {
        "id": tx_id,
        "date": "2026-09-01",
        "amount": -12340,
        "payee_name": payee,
        "memo": None,
        "account_name": "Checking",
        "category_id": category_id,
        "transfer_account_id": None,
        "deleted": False,
    }
    tx.update(extra)
    return tx


def _history() -> list[dict[str, Any]]:
    return [
        _tx(f"h{i}", f"CB CORNER SHOP FACT 0101{i:02d} 525130******2", "c-food") for i in range(3)
    ]


def test_pending_transactions_are_listed_with_currency_amounts() -> None:
    """Pending items carry what an agent needs, amounts in currency units."""
    result = triage.prepare(_history() + [_tx("p1", "Unknown Cafe", memo="lunch")], _CATEGORIES)
    assert result["pending_count"] == 1
    assert result["items"] == [
        {
            "transaction_id": "p1",
            "date": "2026-09-01",
            "amount": -12.34,
            "payee": "Unknown Cafe",
            "memo": "lunch",
            "account": "Checking",
            "suggestion": None,
        }
    ]


def test_known_merchant_gets_a_suggestion() -> None:
    """A merchant seen before under another dated label is suggested from history."""
    pending = _tx("p1", "CB CORNER SHOP FACT 300926 525130******2")
    item = triage.prepare(_history() + [pending], _CATEGORIES)["items"][0]
    assert item["suggestion"] == {
        "category_id": "c-food",
        "category_name": "Groceries",
        "confidence": 1.0,
    }
    assert triage.prepare(_history() + [pending], _CATEGORIES)["suggested_count"] == 1


def test_ambiguous_merchant_gets_no_suggestion() -> None:
    """Below the confidence threshold the agent decides, not the history."""
    history = [_tx("h1", "SHOP", "c-food"), _tx("h2", "SHOP", "c-fun")]
    item = triage.prepare(history + [_tx("p1", "SHOP")], _CATEGORIES, threshold=0.9)["items"][0]
    assert item["suggestion"] is None


def test_transfers_and_deleted_transactions_are_not_pending() -> None:
    """Transfers between accounts need no category; deleted ones do not exist."""
    txs = [
        _tx("t1", "Transfer : Savings", transfer_account_id="acc-2"),
        _tx("t2", "Gone", deleted=True),
    ]
    assert triage.prepare(txs, _CATEGORIES)["pending_count"] == 0


def test_categories_are_listed_once_without_deleted_ones() -> None:
    """The agent gets the category list once, to decide the unsuggested items."""
    result = triage.prepare([_tx("p1", "Unknown Cafe")], _CATEGORIES)
    assert result["categories"] == [
        {"category_id": "c-food", "name": "Groceries", "group": "Everyday"},
        {"category_id": "c-fun", "name": "Leisure", "group": "Everyday"},
    ]


def test_items_are_newest_first_and_paginated_with_a_cursor() -> None:
    """A page holds `limit` items; next_cursor fetches the rest, then is None."""
    txs = [_tx(f"p{i}", f"Shop {i}", date=f"2026-09-{i:02d}") for i in range(1, 6)]
    first = triage.prepare(txs, _CATEGORIES, limit=2)
    assert [i["transaction_id"] for i in first["items"]] == ["p5", "p4"]
    assert first["next_cursor"] is not None
    second = triage.prepare(txs, _CATEGORIES, limit=2, cursor=first["next_cursor"])
    assert [i["transaction_id"] for i in second["items"]] == ["p3", "p2"]
    third = triage.prepare(txs, _CATEGORIES, limit=2, cursor=second["next_cursor"])
    assert [i["transaction_id"] for i in third["items"]] == ["p1"]
    assert third["next_cursor"] is None


def test_long_bank_text_is_truncated() -> None:
    """Payee and memo are untrusted and bounded, so one label cannot flood the context."""
    item = triage.prepare([_tx("p1", "X" * 300, memo="Y" * 300)], _CATEGORIES)["items"][0]
    assert len(item["payee"]) == triage.MAX_TEXT
    assert item["payee"].endswith("…")
    assert len(item["memo"] or "") == triage.MAX_TEXT


def test_invalid_cursor_is_rejected_with_an_actionable_message() -> None:
    """A cursor the server did not issue is refused, saying what to do."""
    try:
        triage.prepare([], _CATEGORIES, cursor="banana")
    except ValueError as error:
        assert "next_cursor" in str(error)
    else:  # pragma: no cover
        raise AssertionError("an invalid cursor must raise")


def test_well_encoded_foreign_cursor_is_rejected() -> None:
    """A valid base64 string that is not one of our cursors is refused too."""
    forged = base64.urlsafe_b64encode(b"page:3").decode()
    try:
        triage.prepare([], _CATEGORIES, cursor=forged)
    except ValueError as error:
        assert "next_cursor" in str(error)
    else:  # pragma: no cover
        raise AssertionError("a foreign cursor must raise")
