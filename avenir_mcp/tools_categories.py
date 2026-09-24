"""Change the category structure: rename or move a category."""

from __future__ import annotations

import logging
from typing import TypedDict

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error

from avenir_mcp import client
from avenir_mcp.app import WRITE_TAG, mcp
from avenir_mcp.confirm import WriteStatus, ask, not_applied

logger = logging.getLogger(__name__)


class CategoryUpdate(TypedDict):
    """The outcome of update_category."""

    status: WriteStatus
    message: str
    category_id: str
    from_name: str
    to_name: str
    from_group: str
    to_group: str
    confirmation: str | None


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Rename or move a category",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
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
) -> CategoryUpdate:
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
    decision = await ask(ctx, budget_id, subject, question, confirmation)
    outcome = not_applied(decision, question)
    if outcome is not None:
        return {**result, **outcome}
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
