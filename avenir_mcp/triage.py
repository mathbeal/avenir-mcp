"""Prepare the classification of pending transactions in one pass.

One download of the budget's transactions serves both as history and as the
list of what is pending: no request per transaction.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any, TypedDict

from avenir_mcp import classifier
from avenir_mcp.client import milliunit_to_amount

MAX_TEXT = 80
DEFAULT_LIMIT = 50


class Suggestion(TypedDict):
    """A category proposed from the payee's history."""

    category_id: str
    category_name: str
    confidence: float


class PendingItem(TypedDict):
    """A transaction waiting for a category."""

    transaction_id: str
    date: str
    amount: float
    payee: str
    memo: str | None
    account: str
    suggestion: Suggestion | None


class CategoryChoice(TypedDict):
    """A category the agent may assign."""

    category_id: str
    name: str
    group: str


class Triage(TypedDict):
    """One page of pending transactions, with what is needed to classify them."""

    pending_count: int
    suggested_count: int
    items: list[PendingItem]
    categories: list[CategoryChoice]
    next_cursor: str | None


def _truncate(text: str) -> str:
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"offset:{offset}".encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        prefix, _, value = base64.urlsafe_b64decode(cursor.encode()).decode().partition(":")
        if prefix != "offset" or not value.isdigit():
            raise ValueError(cursor)
    except (ValueError, binascii.Error, UnicodeDecodeError) as error:
        raise ValueError(
            "Invalid cursor: pass the next_cursor value from the previous page unchanged, "
            "or omit it to start from the first page."
        ) from error
    return int(value)


def _is_pending(tx: dict[str, Any]) -> bool:
    return not tx.get("deleted") and not tx.get("category_id") and not tx.get("transfer_account_id")


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
            "payee": _truncate(tx.get("payee_name") or ""),
            "memo": _truncate(tx["memo"]) if tx.get("memo") else None,
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
