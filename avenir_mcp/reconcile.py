"""Compare an account with the balance the bank shows, and explain the gap.

Pure computation on the budget's transactions: no request to YNAB. Sums are
made in milliunits, so no rounding error can invent a difference.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, TypedDict

from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp.classifier import normalize_payee
from avenir_mcp.client import amount_to_milliunit, milliunit_to_amount
from avenir_mcp.text import untrusted

MAX_LISTED = 50
DUPLICATE_WINDOW_DAYS = 3
DUPLICATE_LOOKBACK_DAYS = 60


@with_config(ConfigDict(use_attribute_docstrings=True))
class Uncleared(TypedDict):
    """A transaction the bank has not shown yet."""

    transaction_id: str
    """YNAB id of the transaction."""
    date: str
    """Date, YYYY-MM-DD."""
    amount: float
    """Amount in currency units, negative for spending."""
    payee: str
    """Payee as imported, cut to 80 characters. Untrusted bank text."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class Analysis(TypedDict):
    """An account compared with the bank's balance."""

    account_id: str
    """The account analysed."""
    bank_balance: float
    """Balance the bank shows, as given."""
    cleared_balance: float
    """Sum of the account's cleared and reconciled transactions in YNAB."""
    working_balance: float
    """Sum of all the account's transactions, cleared or not."""
    difference: float
    """Bank balance minus cleared balance; negative when YNAB counts more money than the bank."""
    to_reconcile_count: int
    """Cleared transactions not yet reconciled."""
    uncleared_count: int
    """Transactions the bank has not shown yet."""
    uncleared: list[Uncleared]
    """Up to 50 of them."""
    explained_by: list[str]
    """Uncleared transactions whose amount equals the difference."""
    possible_duplicates: list[list[str]]
    """Pairs with the same amount and merchant, at most 3 days apart, over the last 60 days."""


def _duplicates(transactions: list[dict[str, Any]]) -> list[list[str]]:
    """Pairs with the same amount and merchant, dated a few days apart."""
    pairs: list[list[str]] = []
    ordered = sorted(transactions, key=lambda tx: tx["date"])
    for i, first in enumerate(ordered):
        for second in ordered[i + 1 :]:
            gap = date.fromisoformat(second["date"]) - date.fromisoformat(first["date"])
            if gap.days > DUPLICATE_WINDOW_DAYS:
                break
            same_payee = normalize_payee(first.get("payee_name") or "") == normalize_payee(
                second.get("payee_name") or ""
            )
            if first["amount"] == second["amount"] and same_payee:
                pairs.append([first["id"], second["id"]])
    return pairs


def analyse(
    account_id: str,
    transactions: list[dict[str, Any]],
    bank_balance: float,
    today: date | None = None,
) -> Analysis:
    """Analyse the account's cleared balance against `bank_balance` (currency units).

    `difference` is bank minus cleared: negative when YNAB counts more money
    than the bank. Duplicates are only looked for in the last 60 days.
    """
    since = ((today or date.today()) - timedelta(days=DUPLICATE_LOOKBACK_DAYS)).isoformat()
    live = [
        tx for tx in transactions if tx.get("account_id") == account_id and not tx.get("deleted")
    ]
    cleared = [tx for tx in live if tx.get("cleared") in ("cleared", "reconciled")]
    uncleared = [tx for tx in live if tx.get("cleared") not in ("cleared", "reconciled")]
    cleared_total = sum(tx["amount"] for tx in cleared)
    difference = amount_to_milliunit(bank_balance) - cleared_total
    return {
        "account_id": account_id,
        "bank_balance": bank_balance,
        "cleared_balance": milliunit_to_amount(cleared_total),
        "working_balance": milliunit_to_amount(sum(tx["amount"] for tx in live)),
        "difference": milliunit_to_amount(difference),
        "to_reconcile_count": sum(1 for tx in cleared if tx.get("cleared") == "cleared"),
        "uncleared_count": len(uncleared),
        "uncleared": [
            {
                "transaction_id": tx["id"],
                "date": tx["date"],
                "amount": milliunit_to_amount(tx["amount"]),
                "payee": untrusted(tx.get("payee_name")),
            }
            for tx in uncleared[:MAX_LISTED]
        ],
        "explained_by": [tx["id"] for tx in uncleared if difference and tx["amount"] == difference],
        "possible_duplicates": _duplicates([tx for tx in live if tx["date"] >= since]),
    }
