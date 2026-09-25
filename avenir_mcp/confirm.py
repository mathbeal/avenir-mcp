"""Confirm a write with the user, then apply and journal it.

A client that supports elicitation asks the user directly; otherwise the first
call returns a preview and a single-use code bound to exactly that preview.
"""

from __future__ import annotations

import logging
from typing import Any, Literal, TypedDict

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error
from mcp import types  # pylint: disable=import-error

from avenir_mcp import client, journal, writes

logger = logging.getLogger(__name__)


CONFIRMATIONS = writes.Confirmations()


WriteStatus = Literal["applied", "confirmation_required", "declined", "nothing_to_do"]


class WriteResult(TypedDict):
    """The outcome of a write tool."""

    status: WriteStatus
    message: str
    changes: list[writes.Change]
    unchanged_count: int
    conflicts: list[str]
    confirmation: str | None
    operation_id: str | None


def result_of(status: WriteStatus, message: str, plan: writes.Plan, **extra: Any) -> WriteResult:
    """Build a write tool's result from a plan; `extra` may set confirmation and operation_id."""
    return {
        "status": status,
        "message": message,
        "changes": plan["changes"],
        "unchanged_count": plan["unchanged_count"],
        "conflicts": plan["conflicts"],
        "confirmation": extra.get("confirmation"),
        "operation_id": extra.get("operation_id"),
    }


def describe(plan: writes.Plan, action: str) -> str:
    """The question put to the user: the first 20 changes, and how many more."""
    lines = [
        f"- {c['date']} {c['payee']} {c['amount']:.2f}: "
        f"{c['from_category'] or 'no category'} → {c['to_category'] or 'no category'}"
        for c in plan["changes"][:20]
    ]
    more = len(plan["changes"]) - len(lines)
    if more > 0:
        lines.append(f"- … and {more} more")
    return f"{action} {len(plan['changes'])} transaction(s)?\n" + "\n".join(lines)


async def ask(
    ctx: Context, budget_id: str, subject: object, question: str, confirmation: str | None
) -> WriteStatus | str:
    """Return "applied" when the user agreed, "declined", or a code to confirm later.

    `subject` is the exact change being confirmed: a code only ever confirms it.
    """
    if confirmation is not None:
        if CONFIRMATIONS.consume(confirmation, budget_id, subject):
            return "applied"
        raise ToolError(
            "This confirmation code is unknown, expired, already used, or was issued for "
            "different changes. Call again without confirmation to get a new preview."
        )
    can_ask = ctx.session.check_client_capability(
        types.ClientCapabilities(elicitation=types.ElicitationCapability())
    )
    if can_ask:
        answer = await ctx.elicit(question, None)
        if answer.action == "accept":
            return "applied"
        if answer.action == "decline":
            return "declined"
        # "cancel": the question was dismissed or could not be shown (a headless
        # client). Nobody said no, so fall back to a code the user can confirm.
    return CONFIRMATIONS.issue(budget_id, subject)


async def write_plan(
    ctx: Context,
    budget_id: str,
    plan: writes.Plan,
    action: str,
    confirmation: str | None,
) -> tuple[WriteResult, str | None]:
    """Confirm and apply a plan; return the result and the new operation id."""
    if not plan["changes"]:
        message = "Nothing to change." + (
            f" {len(plan['conflicts'])} transaction(s) changed since and were left alone."
            if plan["conflicts"]
            else ""
        )
        return result_of("nothing_to_do", message, plan), None
    decision = await ask(ctx, budget_id, plan["changes"], describe(plan, action), confirmation)
    if decision == "declined":
        return result_of("declined", "The user declined: nothing was changed.", plan), None
    if decision != "applied":
        message = (
            "Nothing changed yet. Show these changes to the user; if they agree, call "
            "again with the same arguments and this confirmation code (valid 10 minutes)."
        )
        return result_of("confirmation_required", message, plan, confirmation=decision), None
    await client.set_transaction_categories(
        budget_id, [(c["transaction_id"], c["to_category_id"]) for c in plan["changes"]]
    )
    moves: list[journal.Move] = [
        {
            "transaction_id": c["transaction_id"],
            "from_category_id": c["from_category_id"],
            "to_category_id": c["to_category_id"],
        }
        for c in plan["changes"]
    ]
    operation_id = journal.Journal(journal.default_path()).record(budget_id, "categorize", moves)
    message = f"Applied. undo_operation with operation_id {operation_id} reverts it."
    result = result_of("applied", message, plan, operation_id=operation_id)
    return result, operation_id


class NotApplied(TypedDict):
    """Why a confirmed write did not happen, in a tool result's own fields."""

    status: WriteStatus
    message: str
    confirmation: str | None


def not_applied(decision: WriteStatus | str, question: str) -> NotApplied | None:
    """Turn ask()'s answer into result fields, or None when the write may proceed."""
    if decision == "applied":
        return None
    if decision == "declined":
        return {
            "status": "declined",
            "message": "The user declined: nothing changed.",
            "confirmation": None,
        }
    return {
        "status": "confirmation_required",
        "message": (
            f"Nothing changed yet. {question} If the user agrees, call again with this code."
        ),
        "confirmation": decision,
    }
