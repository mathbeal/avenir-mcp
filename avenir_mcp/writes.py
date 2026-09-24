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

from avenir_mcp.client import milliunit_to_amount
from avenir_mcp.journal import Move

CONFIRMATION_TTL_SECONDS = 600


class Assignment(TypedDict):
    """A category to give to a transaction."""

    transaction_id: str
    category_id: str


class Change(TypedDict):
    """One transaction moving from a category to another."""

    transaction_id: str
    date: str
    amount: float
    payee: str
    from_category_id: str | None
    from_category: str | None
    to_category_id: str | None
    to_category: str | None


class Plan(TypedDict):
    """What an operation would change, and what it leaves alone."""

    changes: list[Change]
    unchanged_count: int
    conflicts: list[str]


def plan_categorization(
    transactions: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    assignments: list[Assignment],
) -> Plan:
    """Work out what assigning these categories would change.

    Raises:
        ValueError: With a message saying what to fix, if an assignment names an
            unknown transaction or category, a transfer, or a transaction twice.
    """
    by_id = {tx["id"]: tx for tx in transactions}
    names = {c["id"]: c["name"] for c in categories}
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
        if category_id not in names:
            raise ValueError(
                f"Category {category_id} is not in this budget: "
                "use a category_id from the categories returned by suggest_categories."
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
                "payee": tx.get("payee_name") or "",
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
                "payee": tx.get("payee_name") or "",
                "from_category_id": move["to_category_id"],
                "from_category": names.get(move["to_category_id"] or ""),
                "to_category_id": before,
                "to_category": names.get(before) if before else None,
            }
        )
    return {"changes": changes, "unchanged_count": 0, "conflicts": conflicts}


def _fingerprint(budget_id: str, changes: list[Change]) -> str:
    moves = sorted((c["transaction_id"], c["to_category_id"] or "") for c in changes)
    payload = json.dumps([budget_id, moves], separators=(",", ":"))
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

    def issue(self, budget_id: str, changes: list[Change]) -> str:
        """Return a new code that confirms these changes, and nothing else."""
        code = secrets.token_urlsafe(8)
        self._issued[code] = (_fingerprint(budget_id, changes), self._clock())
        return code

    def consume(self, code: str, budget_id: str, changes: list[Change]) -> bool:
        """Spend a code: True only if it was issued for these changes and is still fresh."""
        issued = self._issued.pop(code, None)
        if issued is None:
            return False
        fingerprint, issued_at = issued
        fresh = self._clock() - issued_at <= self._ttl
        return fresh and fingerprint == _fingerprint(budget_id, changes)
