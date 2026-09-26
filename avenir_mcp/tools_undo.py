"""Undo an operation recorded in the journal, whatever its kind."""

from __future__ import annotations

import logging

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error
from mcp.types import InputRequiredResult  # pylint: disable=import-error

from avenir_mcp import client, journal, writes
from avenir_mcp.app import WRITE_TAG, mcp
from avenir_mcp.confirm import WriteResult, ask, not_applied, result_of, write_plan

logger = logging.getLogger(__name__)


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Undo an operation",
        "read_only_hint": False,
        "destructive_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
    },
)
async def undo_operation(
    plan_id: str,
    ctx: Context,
    operation_id: str | None = None,
    confirmation: str | None = None,
) -> WriteResult | InputRequiredResult:
    """Undo an operation made through this server: the latest one, or the one named.

    Recategorised transactions go back to their previous category; a
    reconciliation is reverted (statuses and adjustment); a budgeted amount goes
    back to its previous value; created transactions are deleted. Anything
    changed again since the operation is left alone and listed in `conflicts`.
    Confirmation works as for apply_categories.

    Args:
        plan_id: YNAB plan id or 'last-used'.
        ctx: The MCP context, used to ask the user.
        operation_id: Operation to undo; omit for the most recent one.
        confirmation: Code from a previous "confirmation_required" result.

    Returns:
        What was reverted and what was left alone, or an input request the client answers by asking
        the user (protocol 2026-07-28).

    Raises:
        ToolError: If the journal is damaged, no operation of the plan is still in
            effect (with that id), or the confirmation code is refused.
    """
    logger.info("Tool called: undo_operation")
    book = journal.Journal(journal.default_path())
    try:
        entry = book.find(plan_id, operation_id)
    except ValueError as error:
        raise ToolError(str(error)) from error
    if entry is None:
        raise ToolError(
            "Nothing to undo: no operation of this plan is still in effect"
            + (f" with id {operation_id}." if operation_id else ".")
        )
    if entry.kind == "reconcile":
        return await _undo_reconcile(ctx, plan_id, book, entry, confirmation)
    if entry.kind == "budget":
        return await _undo_budget(ctx, plan_id, book, entry, confirmation)
    if entry.kind == "create":
        return await _undo_create(ctx, plan_id, book, entry, confirmation)
    transactions = await client.get_transactions(plan_id)
    categories = await client.get_categories(plan_id)
    plan = writes.plan_undo(transactions, categories, entry.moves)
    result, new_operation = await write_plan(ctx, plan_id, plan, "Undo: recategorise", confirmation)
    if new_operation is not None:
        book.mark_undone(entry.operation_id)
        book.mark_undone(new_operation)
    return result


async def _confirm_undo(
    ctx: Context, plan_id: str, entry: journal.Entry, question: str, confirmation: str | None
) -> WriteResult | InputRequiredResult | None:
    """Ask the user to confirm an undo.

    Args:
        ctx: The MCP context, used to ask the user.
        plan_id: YNAB plan id or 'last-used'.
        entry: The operation to undo.
        question: What the user is asked.
        confirmation: A code from a previous preview, or None.

    Returns:
        None when the user agreed; otherwise what to return instead of undoing.
    """
    decision = await ask(ctx, plan_id, {"undo": entry.operation_id}, question, confirmation)
    if isinstance(decision, InputRequiredResult):
        return decision
    outcome = not_applied(decision, question)
    if outcome is None:
        return None
    return result_of(
        outcome.status, outcome.message, writes.Plan(), confirmation=outcome.confirmation
    )


async def _undo_reconcile(
    ctx: Context,
    plan_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult | InputRequiredResult:
    """Put reconciled transactions back to cleared and delete the adjustment, if any.

    Args:
        ctx: The MCP context, used to ask the user.
        plan_id: YNAB plan id or 'last-used'.
        book: The journal, to mark the operation undone.
        entry: The operation to undo.
        confirmation: A code from a previous preview, or None.

    Returns:
        What was done, or what to return instead when the user did not agree.
    """
    details = entry.details
    statuses = {tx["id"]: tx for tx in await client.get_transactions(plan_id)}
    reverted = [
        tx_id
        for tx_id in details["reconciled_ids"]
        if statuses.get(tx_id, {}).get("cleared") == "reconciled"
    ]
    adjustment = details.get("adjustment_id")
    question = f"Undo reconciliation: mark {len(reverted)} transaction(s) back to cleared" + (
        " and delete the balance adjustment?" if adjustment else "?"
    )
    refused = await _confirm_undo(ctx, plan_id, entry, question, confirmation)
    if refused is not None:
        return refused
    await client.set_transactions_cleared(plan_id, reverted, "cleared")
    if adjustment:
        await client.delete_transaction(plan_id, adjustment)
    book.mark_undone(entry.operation_id)
    return result_of("applied", "Reconciliation undone.", writes.Plan())


async def _undo_budget(
    ctx: Context,
    plan_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult | InputRequiredResult:
    """Set a category's budgeted amount back to what it was, unless it moved since.

    Args:
        ctx: The MCP context, used to ask the user.
        plan_id: YNAB plan id or 'last-used'.
        book: The journal, to mark the operation undone.
        entry: The operation to undo.
        confirmation: A code from a previous preview, or None.

    Returns:
        What was done, or what to return instead when the user did not agree.
    """
    details = entry.details
    categories = await client.get_month_categories(plan_id, details["month"])
    current = next((c for c in categories if c["id"] == details["category_id"]), None)
    if current is None or current["budgeted"] != details["to"]:
        conflict = writes.Plan(conflicts=[details["category_id"]])
        return result_of("nothing_to_do", "The amount changed since: left alone.", conflict)
    previous = client.milliunit_to_amount(details["from"])
    question = f"Undo: set {current['name']} for {details['month']} back to {previous:.2f}?"
    refused = await _confirm_undo(ctx, plan_id, entry, question, confirmation)
    if refused is not None:
        return refused
    await client.set_category_budgeted(plan_id, details["month"], details["category_id"], previous)
    book.mark_undone(entry.operation_id)
    return result_of("applied", "Budgeted amount restored.", writes.Plan())


async def _undo_create(
    ctx: Context,
    plan_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult | InputRequiredResult:
    """Delete the transactions an operation created, those still there.

    Args:
        ctx: The MCP context, used to ask the user.
        plan_id: YNAB plan id or 'last-used'.
        book: The journal, to mark the operation undone.
        entry: The operation to undo.
        confirmation: A code from a previous preview, or None.

    Returns:
        What was done, the ids already gone as conflicts, or what to return instead
        when the user did not agree.
    """
    created = entry.details["transaction_ids"]
    live = {tx["id"] for tx in await client.get_transactions(plan_id) if not tx.get("deleted")}
    present = [tx_id for tx_id in created if tx_id in live]
    gone = [tx_id for tx_id in created if tx_id not in live]
    if not present:
        return result_of(
            "nothing_to_do", "Already deleted: nothing to undo.", writes.Plan(conflicts=gone)
        )
    question = f"Undo: delete the {len(present)} transaction(s) this operation created?"
    refused = await _confirm_undo(ctx, plan_id, entry, question, confirmation)
    if refused is not None:
        return refused
    for tx_id in present:
        await client.delete_transaction(plan_id, tx_id)
    book.mark_undone(entry.operation_id)
    return result_of("applied", "Created transactions deleted.", writes.Plan(conflicts=gone))
