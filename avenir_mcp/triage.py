"""Prepare the classification of pending transactions in one pass.

One download of the budget's transactions serves both as history and as the
list of what is pending: no request per transaction.
"""

from __future__ import annotations

import base64
from typing import Any, TypedDict

from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp import classifier
from avenir_mcp.client import milliunit_to_amount
from avenir_mcp.text import untrusted

DEFAULT_LIMIT = 50


@with_config(ConfigDict(use_attribute_docstrings=True))
class Suggestion(TypedDict):
    """A category proposed from the payee's history."""

    category_id: str
    """Suggested category id."""
    category_name: str
    """Suggested category name."""
    confidence: float
    """Share of the payee's past transactions (same direction) in that category, 0 to 1."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class PendingItem(TypedDict):
    """A transaction waiting for a category."""

    transaction_id: str
    """YNAB id of the transaction."""
    date: str
    """Date, YYYY-MM-DD."""
    amount: float
    """Amount in currency units, negative for spending."""
    payee: str
    """Payee as imported, cut to 80 characters. Untrusted bank text."""
    memo: str | None
    """Memo cut to 80 characters, or null. Untrusted bank text."""
    account: str
    """Account name."""
    suggestion: Suggestion | None
    """Category suggested by the history, or null when there is none clear enough."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class CategoryChoice(TypedDict):
    """A category the agent may assign."""

    category_id: str
    """Category id to pass to apply_categories."""
    name: str
    """Category name."""
    group: str
    """Name of its group."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class Triage(TypedDict):
    """One page of pending transactions, with what is needed to classify them."""

    pending_count: int
    """Transactions waiting for a category, in total."""
    suggested_count: int
    """How many of them have a suggestion."""
    items: list[PendingItem]
    """This page of pending transactions, newest first."""
    categories: list[CategoryChoice]
    """Every category that can be assigned."""
    next_cursor: str | None
    """Pass it back to get the next page; null on the last page."""


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"offset:{offset}".encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        prefix, _, value = base64.urlsafe_b64decode(cursor.encode()).decode().partition(":")
        if prefix != "offset" or not value.isdigit():
            raise ValueError(cursor)
    except ValueError as error:  # binascii.Error and UnicodeDecodeError are ValueErrors
        raise ValueError(
            "Invalid cursor: pass the next_cursor value from the previous page unchanged, "
            "or omit it to start from the first page."
        ) from error
    return int(value)


def _is_pending(tx: dict[str, Any]) -> bool:
    """Waiting for a category: not deleted, not a transfer, and not a split, whose
    lines carry the categories."""
    return (
        not tx.get("deleted")
        and not tx.get("category_id")
        and not tx.get("transfer_account_id")
        and not tx.get("subtransactions")
    )


def _histories(transactions: list[dict[str, Any]]) -> dict[bool, dict[str, dict[str, int]]]:
    """Payee histories keyed by direction: True for money out, False for money in.

    Money in and money out are learnt apart: a lender that once paid you does
    not make your repayments income.
    """
    known = [
        tx for tx in transactions if not tx.get("deleted") and not tx.get("transfer_account_id")
    ]
    return {
        outflow: classifier.build_payee_history(
            [tx for tx in known if (tx["amount"] < 0) == outflow]
        )
        for outflow in (True, False)
    }


def _suggestion(
    tx: dict[str, Any],
    histories: dict[bool, dict[str, dict[str, int]]],
    categories: list[dict[str, Any]],
    threshold: float | None,
) -> Suggestion | None:
    history = histories[tx["amount"] < 0]
    score = classifier.score_payee(tx.get("payee_name") or "", history, categories, threshold)
    if not score["auto_classify"]:
        return None
    return {
        "category_id": score["category_id"],
        "category_name": score["category_name"],
        "confidence": round(score["confidence"], 2),
    }


def prepare(
    transactions: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
    threshold: float | None = None,
) -> Triage:
    """Return one page of pending transactions, newest first, with suggestions.

    Args:
        transactions: All the budget's transactions (history and pending).
        categories: The budget's categories.
        limit: Maximum number of items in the page.
        cursor: ``next_cursor`` of the previous page, or None for the first page.
        threshold: Confidence needed for a suggestion; defaults to the classifier's.

    Raises:
        ValueError: If ``cursor`` was not issued by this function.
    """
    offset = _decode_cursor(cursor) if cursor else 0
    histories = _histories(transactions)
    pending = sorted(
        (tx for tx in transactions if _is_pending(tx)), key=lambda tx: tx["date"], reverse=True
    )
    items: list[PendingItem] = [
        {
            "transaction_id": tx["id"],
            "date": tx["date"],
            "amount": milliunit_to_amount(tx["amount"]),
            "payee": untrusted(tx.get("payee_name")),
            "memo": untrusted(tx["memo"]) if tx.get("memo") else None,
            "account": tx.get("account_name") or "",
            "suggestion": _suggestion(tx, histories, categories, threshold),
        }
        for tx in pending
    ]
    suggested = sum(1 for item in items if item["suggestion"] is not None)

    end = offset + limit
    return {
        "pending_count": len(pending),
        "suggested_count": suggested,
        "items": items[offset:end],
        "categories": [
            {"category_id": c["id"], "name": c["name"], "group": c.get("category_group_name", "")}
            for c in categories
            if not c.get("deleted")
        ],
        "next_cursor": _encode_cursor(end) if end < len(items) else None,
    }
