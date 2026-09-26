"""Plan a change to the budget and confirm it before it happens.

Nothing here talks to YNAB. A plan says exactly what would change; a
confirmation code, issued for one plan, lets a client without elicitation
confirm that plan and no other.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections.abc import Callable
from typing import Any, TypedDict

from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp.client import milliunit_to_amount
from avenir_mcp.journal import Move
from avenir_mcp.text import untrusted
from avenir_mcp.triage import internal_uncategorized

CONFIRMATION_TTL_SECONDS = 600


@with_config(ConfigDict(use_attribute_docstrings=True))
class Assignment(TypedDict):
    """A category to give to a transaction."""

    transaction_id: str
    """Transaction to categorise, from suggest_categories."""
    category_id: str
    """Category to give it."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class Change(TypedDict):
    """One transaction moving from a category to another."""

    transaction_id: str
    """YNAB id of the transaction."""
    date: str
    """Date, YYYY-MM-DD."""
    amount: float
    """Amount in currency units."""
    payee: str
    """Payee as imported. Untrusted bank text."""
    from_category_id: str | None
    """Category id before; null for none."""
    from_category: str | None
    """Category name before; null for none."""
    to_category_id: str | None
    """Category id after; null for none."""
    to_category: str | None
    """Category name after; null for none."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class Plan(TypedDict):
    """What an operation would change, and what it leaves alone."""

    changes: list[Change]
    """Transactions that would change."""
    unchanged_count: int
    """Assignments that change nothing."""
    conflicts: list[str]
    """Ids left alone because they changed since."""


def plan_categorization(
    transactions: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    assignments: list[Assignment],
    off_budget: set[str] | frozenset[str] = frozenset(),
) -> Plan:
    """Work out what assigning these categories would change.

    Raises:
        ValueError: With a message saying what to fix, if an assignment names an
            unknown transaction or category, a transfer, a split, a transaction of
            an off-budget account, YNAB's internal Uncategorized, or a
            transaction twice.
    """
    by_id = {tx["id"]: tx for tx in transactions}
    names = {c["id"]: c["name"] for c in categories}
    uncategorized = internal_uncategorized(categories)
    seen: set[str] = set()
    changes: list[Change] = []
    unchanged = 0
    for assignment in assignments:
        tx_id, category_id = assignment["transaction_id"], assignment["category_id"]
        if tx_id in seen:
            raise ValueError(f"Transaction {tx_id} is assigned twice: keep one assignment.")
        seen.add(tx_id)
        tx = by_id.get(tx_id)
        if tx is None:
            raise ValueError(
                f"Transaction {tx_id} is not in this budget: "
                "use the transaction_id values returned by suggest_categories."
            )
        if category_id in uncategorized:
            raise ValueError(
                f"Category {category_id} is YNAB's internal Uncategorized: choose a real category."
            )
        if category_id not in names:
            raise ValueError(
                f"Category {category_id} is not in this budget: "
                "use a category_id from the categories returned by suggest_categories."
            )
        if tx.get("subtransactions"):
            raise ValueError(
                f"Transaction {tx_id} is split across categories: change its lines in YNAB."
            )
        if tx.get("account_id") in off_budget:
            raise ValueError(
                f"Transaction {tx_id} is on an off-budget account: YNAB gives it no category."
            )
        if tx.get("transfer_account_id"):
            raise ValueError(
                f"Transaction {tx_id} is a transfer between accounts: YNAB gives it no category."
            )
        current = tx.get("category_id")
        if current == category_id:
            unchanged += 1
            continue
        changes.append(
            {
                "transaction_id": tx_id,
                "date": tx["date"],
                "amount": milliunit_to_amount(tx["amount"]),
                "payee": untrusted(tx.get("payee_name")),
                "from_category_id": current,
                "from_category": names.get(current) if current else None,
                "to_category_id": category_id,
                "to_category": names[category_id],
            }
        )
    return {"changes": changes, "unchanged_count": unchanged, "conflicts": []}


def plan_undo(
    transactions: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    moves: list[Move],
) -> Plan:
    """Work out what undoing these moves would change.

    A transaction whose category changed again since the operation is left
    alone and listed in ``conflicts``, so that undo never overwrites later work.
    """
    by_id = {tx["id"]: tx for tx in transactions}
    names = {c["id"]: c["name"] for c in categories}
    changes: list[Change] = []
    conflicts: list[str] = []
    for move in moves:
        tx = by_id.get(move["transaction_id"])
        if tx is None or tx.get("category_id") != move["to_category_id"]:
            conflicts.append(move["transaction_id"])
            continue
        before = move["from_category_id"]
        changes.append(
            {
                "transaction_id": tx["id"],
                "date": tx["date"],
                "amount": milliunit_to_amount(tx["amount"]),
                "payee": untrusted(tx.get("payee_name")),
                "from_category_id": move["to_category_id"],
                "from_category": names.get(move["to_category_id"] or ""),
                "to_category_id": before,
                "to_category": names.get(before) if before else None,
            }
        )
    return {"changes": changes, "unchanged_count": 0, "conflicts": conflicts}


def fingerprint(budget_id: str, subject: object) -> str:
    """Hash what is being confirmed; the order of a list of changes does not matter."""
    if isinstance(subject, list):
        subject = sorted(json.dumps(item, sort_keys=True) for item in subject)
    payload = json.dumps([budget_id, subject], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


class Confirmations:
    """Single-use confirmation codes, each bound to one exact plan."""

    def __init__(
        self,
        ttl_seconds: float = CONFIRMATION_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._issued: dict[str, tuple[str, float]] = {}

    def issue(self, budget_id: str, subject: object) -> str:
        """Return a new code that confirms this subject (JSON data), and nothing else.

        Expired codes are dropped first, so previews never confirmed do not pile up.
        """
        now = self._clock()
        self._issued = {c: v for c, v in self._issued.items() if now - v[1] <= self._ttl}
        code = secrets.token_urlsafe(8)
        self._issued[code] = (fingerprint(budget_id, subject), now)
        return code

    def consume(self, code: str, budget_id: str, subject: object) -> bool:
        """Spend a code: True only if it was issued for this subject and is still fresh."""
        issued = self._issued.pop(code, None)
        if issued is None:
            return False
        expected, issued_at = issued
        fresh = self._clock() - issued_at <= self._ttl
        return fresh and expected == fingerprint(budget_id, subject)
