"""Undo an operation recorded in the journal, whatever its kind."""

from __future__ import annotations

import logging

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error

from avenir_mcp import client, journal, writes
from avenir_mcp.app import WRITE_TAG, mcp
from avenir_mcp.confirm import WriteResult, ask, not_applied, result_of, write_plan

logger = logging.getLogger(__name__)

_EMPTY: writes.Plan = {"changes": [], "unchanged_count": 0, "conflicts": []}


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Undo an operation",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def undo_operation(
    budget_id: str,
    ctx: Context,
    operation_id: str | None = None,
    confirmation: str | None = None,
) -> WriteResult:
    """Undo an operation made through this server: the latest one, or the one named.

    Recategorised transactions go back to their previous category; a
    reconciliation is reverted (statuses and adjustment); a budgeted amount goes
    back to its previous value; created transactions are deleted. Anything
    changed again since the operation is left alone and listed in `conflicts`.
    Confirmation works as for apply_categories.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        operation_id: Operation to undo; omit for the most recent one.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: undo_operation")
    book = journal.Journal(journal.default_path())
    entry = book.find(budget_id, operation_id)
    if entry is None:
        raise ToolError(
            "Nothing to undo: no operation of this budget is still in effect"
            + (f" with id {operation_id}." if operation_id else ".")
        )
    if entry["kind"] == "reconcile":
        return await _undo_reconcile(ctx, budget_id, book, entry, confirmation)
    if entry["kind"] == "budget":
        return await _undo_budget(ctx, budget_id, book, entry, confirmation)
    if entry["kind"] == "create":
        return await _undo_create(ctx, budget_id, book, entry, confirmation)
    transactions = await client.get_transactions(budget_id)
    categories = await client.get_categories(budget_id)
    plan = writes.plan_undo(transactions, categories, entry["moves"])
    result, new_operation = await write_plan(
        ctx, budget_id, plan, "Undo: recategorise", confirmation
    )
    if new_operation is not None:
        book.mark_undone(entry["operation_id"])
        book.mark_undone(new_operation)
    return result


async def _confirm_undo(
    ctx: Context, budget_id: str, entry: journal.Entry, question: str, confirmation: str | None
) -> WriteResult | None:
    """None when the user agreed; otherwise the result saying why nothing happened."""
    decision = await ask(ctx, budget_id, {"undo": entry["operation_id"]}, question, confirmation)
    outcome = not_applied(decision, question)
    if outcome is None:
        return None
    return result_of(
        outcome["status"], outcome["message"], _EMPTY, confirmation=outcome["confirmation"]
    )


async def _undo_reconcile(
    ctx: Context,
    budget_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult:
    """Put reconciled transactions back to cleared and delete the adjustment, if any."""
    details = entry["details"]
    statuses = {tx["id"]: tx for tx in await client.get_transactions(budget_id)}
    reverted = [
        tx_id
        for tx_id in details["reconciled_ids"]
        if statuses.get(tx_id, {}).get("cleared") == "reconciled"
    ]
    adjustment = details.get("adjustment_id")
    question = f"Undo reconciliation: mark {len(reverted)} transaction(s) back to cleared" + (
        " and delete the balance adjustment?" if adjustment else "?"
    )
    refused = await _confirm_undo(ctx, budget_id, entry, question, confirmation)
    if refused is not None:
        return refused
    await client.set_transactions_cleared(budget_id, reverted, "cleared")
    if adjustment:
        await client.delete_transaction(budget_id, adjustment)
    book.mark_undone(entry["operation_id"])
    return result_of("applied", "Reconciliation undone.", _EMPTY)


async def _undo_budget(
    ctx: Context,
    budget_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult:
    """Set a category's budgeted amount back to what it was, unless it moved since."""
    details = entry["details"]
    categories = await client.get_month_categories(budget_id, details["month"])
    current = next((c for c in categories if c["id"] == details["category_id"]), None)
    if current is None or current["budgeted"] != details["to"]:
        conflict: writes.Plan = {**_EMPTY, "conflicts": [details["category_id"]]}
        return result_of("nothing_to_do", "The amount changed since: left alone.", conflict)
    previous = client.milliunit_to_amount(details["from"])
    question = f"Undo: set {current['name']} for {details['month']} back to {previous:.2f}?"
    refused = await _confirm_undo(ctx, budget_id, entry, question, confirmation)
    if refused is not None:
        return refused
    await client.set_category_budgeted(
        budget_id, details["month"], details["category_id"], previous
    )
    book.mark_undone(entry["operation_id"])
    return result_of("applied", "Budgeted amount restored.", _EMPTY)


async def _undo_create(
    ctx: Context,
    budget_id: str,
    book: journal.Journal,
    entry: journal.Entry,
    confirmation: str | None,
) -> WriteResult:
    """Delete the transactions an operation created, those still there."""
    created = entry["details"]["transaction_ids"]
    live = {tx["id"] for tx in await client.get_transactions(budget_id) if not tx.get("deleted")}
    present = [tx_id for tx_id in created if tx_id in live]
    gone = [tx_id for tx_id in created if tx_id not in live]
    if not present:
        conflict: writes.Plan = {**_EMPTY, "conflicts": gone}
        return result_of("nothing_to_do", "Already deleted: nothing to undo.", conflict)
    question = f"Undo: delete the {len(present)} transaction(s) this operation created?"
    refused = await _confirm_undo(ctx, budget_id, entry, question, confirmation)
    if refused is not None:
        return refused
    for tx_id in present:
        await client.delete_transaction(budget_id, tx_id)
    book.mark_undone(entry["operation_id"])
    return result_of("applied", "Created transactions deleted.", {**_EMPTY, "conflicts": gone})
