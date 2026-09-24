"""Tests for writes.py — planning a change and confirming it before it happens."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import writes

_CATEGORIES: list[dict[str, Any]] = [
    {"id": "c-food", "name": "Groceries"},
    {"id": "c-fun", "name": "Leisure"},
]


def _tx(tx_id: str, category_id: str | None = None, **extra: Any) -> dict[str, Any]:
    tx: dict[str, Any] = {
        "id": tx_id,
        "date": "2026-09-01",
        "amount": -12340,
        "payee_name": "Corner Shop",
        "category_id": category_id,
        "transfer_account_id": None,
    }
    tx.update(extra)
    return tx


# ---------------------------------------------------------------------------
# plan_categorization
# ---------------------------------------------------------------------------


def test_plan_lists_each_change_with_before_and_after() -> None:
    """The preview says what moves from where to where, amounts in currency units."""
    plan = writes.plan_categorization(
        [_tx("t1"), _tx("t2", "c-fun")],
        _CATEGORIES,
        [
            {"transaction_id": "t1", "category_id": "c-food"},
            {"transaction_id": "t2", "category_id": "c-food"},
        ],
    )
    assert plan["changes"] == [
        {
            "transaction_id": "t1",
            "date": "2026-09-01",
            "amount": -12.34,
            "payee": "Corner Shop",
            "from_category_id": None,
            "from_category": None,
            "to_category_id": "c-food",
            "to_category": "Groceries",
        },
        {
            "transaction_id": "t2",
            "date": "2026-09-01",
            "amount": -12.34,
            "payee": "Corner Shop",
            "from_category_id": "c-fun",
            "from_category": "Leisure",
            "to_category_id": "c-food",
            "to_category": "Groceries",
        },
    ]
    assert plan["unchanged_count"] == 0


def test_plan_skips_assignments_that_change_nothing() -> None:
    """Assigning a transaction to its current category is not a change."""
    plan = writes.plan_categorization(
        [_tx("t1", "c-food")], _CATEGORIES, [{"transaction_id": "t1", "category_id": "c-food"}]
    )
    assert not plan["changes"]
    assert plan["unchanged_count"] == 1


def test_plan_rejects_an_unknown_transaction() -> None:
    """An id that is not in the budget is refused, naming it."""
    with pytest.raises(ValueError, match="t404.*suggest_categories"):
        writes.plan_categorization(
            [], _CATEGORIES, [{"transaction_id": "t404", "category_id": "c-food"}]
        )


def test_plan_rejects_an_unknown_category() -> None:
    """A category id that is not in the budget is refused, naming it."""
    with pytest.raises(ValueError, match="c-404.*categories"):
        writes.plan_categorization(
            [_tx("t1")], _CATEGORIES, [{"transaction_id": "t1", "category_id": "c-404"}]
        )


def test_plan_rejects_a_transfer() -> None:
    """Transfers between accounts take no category in YNAB."""
    with pytest.raises(ValueError, match="transfer"):
        writes.plan_categorization(
            [_tx("t1", transfer_account_id="acc-2")],
            _CATEGORIES,
            [{"transaction_id": "t1", "category_id": "c-food"}],
        )


def test_plan_rejects_the_same_transaction_twice() -> None:
    """Two assignments for one transaction are ambiguous."""
    with pytest.raises(ValueError, match="t1.*twice"):
        writes.plan_categorization(
            [_tx("t1")],
            _CATEGORIES,
            [
                {"transaction_id": "t1", "category_id": "c-food"},
                {"transaction_id": "t1", "category_id": "c-fun"},
            ],
        )


# ---------------------------------------------------------------------------
# Confirmations — single-use codes bound to one exact plan
# ---------------------------------------------------------------------------


def _changes(to: str = "c-food") -> list[writes.Change]:
    return writes.plan_categorization(
        [_tx("t1")], _CATEGORIES, [{"transaction_id": "t1", "category_id": to}]
    )["changes"]


def test_confirmation_code_accepts_the_plan_it_was_issued_for_once() -> None:
    """A code confirms its own plan, and only once."""
    confirmations = writes.Confirmations()
    code = confirmations.issue("b1", _changes())
    assert confirmations.consume(code, "b1", _changes()) is True
    assert confirmations.consume(code, "b1", _changes()) is False


def test_confirmation_code_refuses_a_different_plan() -> None:
    """A code issued for one change cannot confirm another."""
    confirmations = writes.Confirmations()
    code = confirmations.issue("b1", _changes("c-food"))
    assert confirmations.consume(code, "b1", _changes("c-fun")) is False
    assert confirmations.consume(code, "b2", _changes("c-food")) is False


def test_confirmation_code_expires() -> None:
    """A code older than its lifetime is refused."""
    now = [1000.0]
    confirmations = writes.Confirmations(ttl_seconds=600, clock=lambda: now[0])
    code = confirmations.issue("b1", _changes())
    now[0] += 601
    assert confirmations.consume(code, "b1", _changes()) is False


def test_unknown_confirmation_code_is_refused() -> None:
    """A code the server never issued confirms nothing."""
    assert writes.Confirmations().consume("made-up", "b1", _changes()) is False


def test_confirmation_code_can_bind_any_json_subject() -> None:
    """A code can confirm a change other than a list of transactions."""
    confirmations = writes.Confirmations()
    rename = {"category_id": "c1", "name": "Pharmacy"}
    code = confirmations.issue("b1", rename)
    assert confirmations.consume(code, "b1", {"category_id": "c1", "name": "Other"}) is False
    code = confirmations.issue("b1", rename)
    assert confirmations.consume(code, "b1", dict(rename)) is True
