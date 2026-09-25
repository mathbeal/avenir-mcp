"""Change categories: create, rename or move one, set the amount budgeted for a month."""

from __future__ import annotations

import logging
from typing import TypedDict

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error
from mcp.types import InputRequiredResult  # pylint: disable=import-error
from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp import app, client, journal
from avenir_mcp.app import WRITE_TAG, check_month, mcp
from avenir_mcp.confirm import WriteStatus, gate

logger = logging.getLogger(__name__)


@with_config(ConfigDict(use_attribute_docstrings=True))
class CategoryUpdate(TypedDict):
    """The outcome of update_category."""

    status: WriteStatus
    """Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the
    user agrees), declined (the user said no), or nothing_to_do.
    """
    message: str
    """What happened and what to do next, for the agent to relay."""
    category_id: str
    """The category changed."""
    from_name: str
    """Name before."""
    to_name: str
    """Name after."""
    from_group: str
    """Group before."""
    to_group: str
    """Group after."""
    confirmation: str | None
    """Single-use code confirming exactly this preview, valid 10 minutes; null unless status is
    confirmation_required.
    """


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Rename or move a category",
        "read_only_hint": False,
        "destructive_hint": True,
        "idempotent_hint": True,
        "open_world_hint": True,
    },
)
async def update_category(  # pylint: disable=too-many-arguments,too-many-locals
    budget_id: str,
    category_id: str,
    ctx: Context,
    *,
    name: str | None = None,
    category_group_id: str | None = None,
    confirmation: str | None = None,
) -> CategoryUpdate | InputRequiredResult:
    """Rename a category and/or move it to another group, after the user confirms.

    Transactions and amounts stay attached to the category. Confirmation works as
    for apply_categories. To revert, call again with the previous name and group,
    which the result gives.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        category_id: Category to change (from suggest_categories or list_category_groups).
        name: New name; omit to keep it.
        category_group_id: Group to move it to (from list_category_groups); omit to keep it.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: update_category")
    categories = {c["id"]: c for c in await client.get_categories(budget_id)}
    groups = {g["id"]: g["name"] for g in await client.get_category_groups(budget_id)}
    category = categories.get(category_id)
    if category is None:
        raise ToolError(
            f"Category {category_id} is not in this budget: "
            "use a category_id from suggest_categories."
        )
    if category_group_id is not None and category_group_id not in groups:
        raise ToolError(
            f"Group {category_group_id} is not in this budget: "
            "use an id from list_category_groups."
        )
    if name is not None and not name.strip():
        raise ToolError("The new name is empty: give a name, or omit it to keep the current one.")
    new_name = name.strip() if name is not None else category["name"]
    new_group = category_group_id or category["category_group_id"]
    result: CategoryUpdate = {
        "status": "nothing_to_do",
        "message": "Nothing to change.",
        "category_id": category_id,
        "from_name": category["name"],
        "to_name": new_name,
        "from_group": category.get("category_group_name", ""),
        "to_group": groups.get(new_group, ""),
        "confirmation": None,
    }
    if new_name == category["name"] and new_group == category["category_group_id"]:
        return result
    subject = {"category_id": category_id, "name": new_name, "group": new_group}
    question = (
        f"Change category '{result['from_name']}' ({result['from_group']}) "
        f"to '{new_name}' ({result['to_group']})?"
    )
    stop = await gate(ctx, budget_id, subject, question, confirmation)
    if stop is not None:
        return stop if isinstance(stop, InputRequiredResult) else {**result, **stop}
    await client.update_category(
        budget_id,
        category_id,
        name=new_name if new_name != category["name"] else None,
        category_group_id=new_group if new_group != category["category_group_id"] else None,
    )
    return {
        **result,
        "status": "applied",
        "message": "Applied. To revert, call update_category with the previous name and group.",
    }


@with_config(ConfigDict(use_attribute_docstrings=True))
class BudgetChange(TypedDict):
    """The outcome of set_category_budget."""

    status: WriteStatus
    """Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the
    user agrees), declined (the user said no), or nothing_to_do.
    """
    message: str
    """What happened and what to do next, for the agent to relay."""
    category_id: str
    """The category changed."""
    category: str
    """Category name."""
    month: str
    """Month changed, YYYY-MM-01 ('current' is resolved)."""
    from_amount: float
    """Amount budgeted before."""
    to_amount: float
    """Amount budgeted after."""
    confirmation: str | None
    """Single-use code confirming exactly this preview, valid 10 minutes; null unless status is
    confirmation_required.
    """
    operation_id: str | None
    """Journal id of the applied operation, for undo_operation; null unless status is applied."""


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Set a category's budgeted amount",
        "read_only_hint": False,
        "destructive_hint": True,
        "idempotent_hint": True,
        "open_world_hint": True,
    },
)
async def set_category_budget(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    budget_id: str,
    month: str,
    category_id: str,
    amount: float,
    ctx: Context,
    confirmation: str | None = None,
) -> BudgetChange | InputRequiredResult:
    """Set the amount budgeted ("Assigned") in a category for a month, after the user confirms.

    The amount is absolute, in currency units, not a change. The result gives the
    amount before and after; undo_operation restores the previous one.
    Confirmation works as for apply_categories.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        month: 'YYYY-MM-01' or 'current'.
        category_id: Category (from get_category_balances or suggest_categories).
        amount: New budgeted amount, in currency units.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: set_category_budget(month=%r)", month)
    check_month(month)
    month = app.resolve_month(month)
    categories = {c["id"]: c for c in await client.get_month_categories(budget_id, month)}
    category = categories.get(category_id)
    if category is None:
        raise ToolError(
            f"Category {category_id} is not in this budget: "
            "use a category_id from get_category_balances."
        )
    before, after = category["budgeted"], client.amount_to_milliunit(amount)
    result: BudgetChange = {
        "status": "nothing_to_do",
        "message": "Nothing to change.",
        "category_id": category_id,
        "category": category["name"],
        "month": month,
        "from_amount": client.milliunit_to_amount(before),
        "to_amount": client.milliunit_to_amount(after),
        "confirmation": None,
        "operation_id": None,
    }
    if before == after:
        return result
    question = (
        f"Budget {category['name']} for {month}: "
        f"{result['from_amount']:.2f} → {result['to_amount']:.2f}?"
    )
    subject = {"category": category_id, "month": month, "amount": after}
    stop = await gate(ctx, budget_id, subject, question, confirmation)
    if stop is not None:
        return stop if isinstance(stop, InputRequiredResult) else {**result, **stop}
    await client.set_category_budgeted(budget_id, month, category_id, amount)
    operation_id = journal.Journal(journal.default_path()).record(
        budget_id,
        "budget",
        [],
        {"month": month, "category_id": category_id, "from": before, "to": after},
    )
    return {
        **result,
        "status": "applied",
        "message": f"Applied. undo_operation with operation_id {operation_id} reverts it.",
        "operation_id": operation_id,
    }


@with_config(ConfigDict(use_attribute_docstrings=True))
class NewCategory(TypedDict):
    """The outcome of create_category."""

    status: WriteStatus
    """Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the
    user agrees), declined (the user said no), or nothing_to_do.
    """
    message: str
    """What happened and what to do next, for the agent to relay."""
    name: str
    """Name of the new category, trimmed."""
    group: str
    """Group it goes in."""
    category_id: str | None
    """YNAB id of the new category; null until applied."""
    confirmation: str | None
    """Single-use code confirming exactly this preview, valid 10 minutes; null unless status is
    confirmation_required.
    """


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Create a category",
        "read_only_hint": False,
        "destructive_hint": False,
        "idempotent_hint": False,
        "open_world_hint": True,
    },
)
async def create_category(
    budget_id: str,
    category_group_id: str,
    name: str,
    ctx: Context,
    confirmation: str | None = None,
) -> NewCategory | InputRequiredResult:
    """Create a category in a group, after the user confirms.

    YNAB's API cannot delete a category: to undo, hide it in YNAB. A name already
    used in the group is refused. Confirmation works as for apply_categories.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        category_group_id: Group to create it in (from list_category_groups).
        name: Name of the new category.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: create_category")
    groups = {g["id"]: g["name"] for g in await client.get_category_groups(budget_id)}
    if category_group_id not in groups:
        raise ToolError(
            f"Group {category_group_id} is not in this budget: "
            "use an id from list_category_groups."
        )
    new_name = name.strip()
    if not new_name:
        raise ToolError("The name is empty: give the new category a name.")
    taken = {
        c["name"].casefold()
        for c in await client.get_categories(budget_id)
        if c.get("category_group_id") == category_group_id
    }
    if new_name.casefold() in taken:
        raise ToolError(f"{new_name!r} already exists in {groups[category_group_id]}.")
    result: NewCategory = {
        "status": "applied",
        "message": "",
        "name": new_name,
        "group": groups[category_group_id],
        "category_id": None,
        "confirmation": None,
    }
    question = f"Create category '{new_name}' in {result['group']}?"
    subject = {"group": category_group_id, "name": new_name}
    stop = await gate(ctx, budget_id, subject, question, confirmation)
    if stop is not None:
        return stop if isinstance(stop, InputRequiredResult) else {**result, **stop}
    created = await client.create_category(budget_id, category_group_id, new_name)
    return {**result, "message": "Created.", "category_id": created["id"]}
