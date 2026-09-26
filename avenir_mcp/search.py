"""Find transactions by account, amount and dates, whatever their category.

Nothing here talks to YNAB. suggest_categories only shows what waits for a
category; matching a receipt, or checking a payment, needs the transactions
YNAB already categorised too.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp.client import amount_to_milliunit
from avenir_mcp.model import Model
from avenir_mcp.triage import Line, line_fields

MAX_DAYS = 366
DEFAULT_LIMIT = 50


class Match(Line):
    """A transaction found, as an agent needs it."""

    category: str | None
    """Category name; null when it has none or is split."""
    split: bool
    """True when the transaction is split: its lines carry the categories."""
    cleared: str
    """cleared, uncleared or reconciled."""
    approved: bool
    """False while it waits for review in YNAB."""


class Found(Model):
    """The transactions found."""

    transactions: list[Match]
    """Newest first."""
    truncated: bool
    """True when more transactions match than the limit: narrow the search."""


def check(
    since: date,
    until: date | None,
    account_ids: list[str] | None,
    names: dict[str, str],
) -> None:
    """Refuse a search that cannot be meant, or would read too much.

    Args:
        since: First date.
        until: Last date, or None for no end.
        account_ids: Accounts to search, or None for all.
        names: The budget's account names by id.

    Raises:
        ValueError: If the dates are reversed, span more than MAX_DAYS, or an
            account is not in the budget.
    """
    if until is not None:
        if until < since:
            raise ValueError(f"until_date {until} is before since_date {since}: swap them.")
        if (until - since).days > MAX_DAYS:
            raise ValueError(f"The dates span more than {MAX_DAYS} days: search a shorter period.")
    unknown = [a for a in account_ids or [] if a not in names]
    if unknown:
        raise ValueError(
            f"Account {unknown[0]} is not in this budget: use an id from list_accounts."
        )


def _categorisation(tx: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    """Say how a transaction is categorised and where it stands.

    Args:
        tx: A YNAB transaction.
        labels: The budget's category names by id.

    Returns:
        category, split, cleared and approved.
    """
    split = any(not sub.get("deleted") for sub in tx.get("subtransactions") or [])
    category = tx.get("category_id")
    return {
        "category": None if split or not category else labels.get(category),
        "split": split,
        "cleared": tx.get("cleared", "uncleared"),
        "approved": bool(tx.get("approved")),
    }


def find(  # pylint: disable=too-many-arguments
    transactions: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    *,
    since: date,
    until: date | None = None,
    amount: float | None = None,
    account_ids: list[str] | None = None,
    limit: int = DEFAULT_LIMIT,
) -> Found:
    """Find the transactions matching the filters, newest first.

    Args:
        transactions: The budget's transactions; deleted ones are never found.
        accounts: The budget's accounts.
        categories: The budget's categories.
        since: First date, included.
        until: Last date, included; None for no end.
        amount: Exact amount in currency units, or None for any.
        account_ids: Accounts to search, or None for all.
        limit: Maximum number of transactions returned.

    Returns:
        The matches, and whether more exist than the limit.

    Raises:
        ValueError: With a message saying what to fix, if the dates are reversed or
            span more than a year, or an account is not in the budget.
    """
    names = {a["id"]: a["name"] for a in accounts}
    check(since, until, account_ids, names)
    wanted = amount_to_milliunit(amount) if amount is not None else None
    labels = {c["id"]: c["name"] for c in categories}
    first, last = since.isoformat(), until.isoformat() if until else None
    kept = [
        tx
        for tx in transactions
        if not tx.get("deleted")
        and tx["date"] >= first
        and (last is None or tx["date"] <= last)
        and (wanted is None or tx["amount"] == wanted)
        and (account_ids is None or tx["account_id"] in account_ids)
    ]
    kept.sort(key=lambda tx: tx["date"], reverse=True)
    matches = [Match(**line_fields(tx), **_categorisation(tx, labels)) for tx in kept[:limit]]
    return Found(transactions=matches, truncated=len(kept) > limit)
