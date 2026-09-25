"""Tools close to the YNAB API: budgets, accounts, categories, single transactions."""

from __future__ import annotations

import logging
from typing import Any

from avenir_mcp import analytics, client
from avenir_mcp.app import WRITE_TAG, check_month, mcp

logger = logging.getLogger(__name__)


@mcp.tool(
    annotations={
        "title": "List budgets",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def list_budgets() -> list[dict[str, Any]]:
    """List all YNAB budgets accessible with the current API key.

    Returns a list of budget dicts with id, name, first_month, last_month.
    Use the budget id (or 'last-used') in subsequent tool calls.
    """
    logger.info("Tool called: list_budgets()")
    return await client.get_budgets()


@mcp.tool(
    annotations={
        "title": "Category balances for a month",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_category_balances(
    budget_id: str,
    month: str = "current",
    include_empty: bool = False,
) -> list[analytics.CategoryBalance]:
    """Budgeted, spent (activity) and available (balance) per category for a month.

    Amounts in currency units; activity is negative for spending. Hidden and
    internal categories are left out, and so are categories with nothing
    budgeted, spent or available unless include_empty is true. Use
    get_budget_vs_actual for the share of each budget consumed.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        month: 'YYYY-MM-01' or 'current'.
        include_empty: Also list categories with no amount at all.
    """
    logger.info("Tool called: get_category_balances(month=%r)", month)
    check_month(month)
    categories = await client.get_month_categories(budget_id, month)
    return analytics.category_balances(categories, include_empty=include_empty)


@mcp.tool(
    annotations={
        "title": "Month summary",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_monthly_summary(
    budget_id: str,
    month: str = "current",
) -> analytics.MonthOverview:
    """A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

    Amounts in currency units; activity is negative for spending. Only
    overspent categories are listed; use get_category_balances for all of them.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        month: 'YYYY-MM-01' or 'current'.
    """
    logger.info("Tool called: get_monthly_summary(month=%r)", month)
    check_month(month)
    return analytics.month_overview(await client.get_month(budget_id, month))


@mcp.tool(
    annotations={
        "title": "Budget vs actual",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_budget_vs_actual(
    budget_id: str,
    month: str = "current",
) -> list[dict[str, Any]]:
    """Return a budget-vs-actual breakdown with utilisation percentage per category.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        month: ISO month 'YYYY-MM-01' or 'current'.

    Each item in the returned list contains:
    - id, name — category identifiers
    - budgeted, actual, balance — amounts in euros
    - utilization_pct — percentage of budget consumed (> 100 means over-budget)
    """
    logger.info("Tool called: get_budget_vs_actual(month=%r)", month)
    check_month(month)
    month_cats = await client.get_month_categories(budget_id, month)
    return analytics.budget_vs_actual(month_cats)


@mcp.tool(
    annotations={
        "title": "Spending trends",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_spending_trends(
    budget_id: str,
    months_count: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """Return monthly spending trends per category over the last N months.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        months_count: Number of past months to include (default 3).

    Returns a dict mapping category name to a chronological list of
    {month, amount} dicts (amounts in euros).
    """
    logger.info(
        "Tool called: get_spending_trends(budget_id=%r, months_count=%d)",
        budget_id,
        months_count,
    )
    # Fetch the list of available months and pick the last N
    all_months = await client.get_months(budget_id)
    recent_months = all_months[-months_count:]

    months_data: list[tuple[str, list[dict[str, Any]]]] = []
    for m in recent_months:
        label = m["month"]
        cats = await client.get_month_categories(budget_id, label)
        months_data.append((label, cats))

    return analytics.spending_trends(months_data)


@mcp.tool(
    annotations={
        "title": "List category groups",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def list_category_groups(budget_id: str) -> list[dict[str, Any]]:
    """List the category groups a new category can be created in.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.

    Returns a list of {id, name} dicts (hidden, deleted and system groups
    excluded). Pass a group id to create_category.
    """
    logger.info("Tool called: list_category_groups(budget_id=%r)", budget_id)
    return await client.get_category_groups(budget_id)


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Create a category",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def create_category(budget_id: str, category_group_id: str, name: str) -> dict[str, Any]:
    """Create a new category in a YNAB budget.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        category_group_id: Group UUID, from list_category_groups.
        name: Name of the new category.

    Returns the created category dict (its id can be used with apply_categories).
    """
    logger.info(
        "Tool called: create_category(budget_id=%r, category_group_id=%r, name=%r)",
        budget_id,
        category_group_id,
        name,
    )
    return await client.create_category(budget_id, category_group_id, name)


@mcp.tool(
    annotations={
        "title": "List accounts",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def list_accounts(budget_id: str) -> list[dict[str, Any]]:
    """List the budget's accounts with their current balances (in euros).

    Args:
        budget_id: YNAB budget UUID or 'last-used'.

    Returns a list of {id, name, type, on_budget, closed, balance,
    cleared_balance, uncleared_balance}. Use it to reconcile YNAB with the bank.
    """
    logger.info("Tool called: list_accounts(budget_id=%r)", budget_id)
    return await client.get_accounts(budget_id)


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Create transactions",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def create_transactions(
    budget_id: str, account_id: str, transactions: list[dict[str, Any]]
) -> dict[str, Any]:
    """Create cleared transactions on an account (e.g. to fill a bank-import gap).

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        account_id: Account UUID, from list_accounts.
        transactions: Items with date ('YYYY-MM-DD'), amount (euros, negative
            for outflows), payee_name, and optional memo, category_id and
            import_id (max 36 chars; items whose import_id already exists are
            skipped, so re-running is safe).

    Returns {created, transaction_ids, duplicate_import_ids}.
    """
    logger.info(
        "Tool called: create_transactions(budget_id=%r, account_id=%r, n=%d)",
        budget_id,
        account_id,
        len(transactions),
    )
    return await client.create_transactions(budget_id, account_id, transactions)


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Approve transactions",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def approve_transactions(budget_id: str, tx_ids: list[str]) -> dict[str, int]:
    """Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

    Only approve transactions whose category has been checked.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        tx_ids: Transaction UUIDs to approve.

    Returns {approved: count}.
    """
    logger.info("Tool called: approve_transactions(budget_id=%r, n=%d)", budget_id, len(tx_ids))
    return await client.approve_transactions(budget_id, tx_ids)
