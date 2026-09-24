"""Financial analytics computed from YNAB data — pure functions, no I/O."""

from __future__ import annotations

import logging
from typing import Any

from avenir_mcp import client

logger = logging.getLogger(__name__)


def budget_vs_actual(
    month_categories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute budget-vs-actual for each category in a given month.

    Args:
        month_categories: List of YNAB category dicts for a specific month,
            each containing ``budgeted`` and ``activity`` in milliunits.

    Returns:
        List of dicts with human-readable amounts and utilisation percentage:

        - ``id``, ``name`` — category identifiers
        - ``budgeted`` — budgeted amount (€)
        - ``actual`` — amount spent, always positive for display (€)
        - ``balance`` — remaining budget (€)
        - ``utilization_pct`` — 0–100+ (> 100 means over-budget); 0 if budgeted=0

    Examples:
        >>> cat = {"id": "c1", "name": "Loyer", "budgeted": 500000,
        ...        "activity": -400000, "balance": 100000}
        >>> budget_vs_actual([cat])[0]["utilization_pct"]
        80.0
    """
    results = []
    for cat in month_categories:
        budgeted_mu = cat.get("budgeted", 0)
        activity_mu = cat.get("activity", 0)
        balance_mu = cat.get("balance", 0)
        budgeted = client.milliunit_to_amount(budgeted_mu)
        actual = client.milliunit_to_amount(abs(activity_mu))
        balance = client.milliunit_to_amount(balance_mu)

        if budgeted == 0.0:
            utilization_pct = 0.0
        else:
            utilization_pct = round(actual / budgeted * 100, 1)

        results.append(
            {
                "id": cat.get("id", ""),
                "name": cat.get("name", ""),
                "budgeted": budgeted,
                "actual": actual,
                "balance": balance,
                "utilization_pct": utilization_pct,
            }
        )
    return results


def spending_trends(
    months_data: list[tuple[str, list[dict[str, Any]]]],
) -> dict[str, list[dict[str, Any]]]:
    """Build a time-series of spending per category across multiple months.

    Args:
        months_data: List of ``(month_label, month_categories)`` tuples,
            ordered chronologically.  Each element is a ``(str, list)`` pair
            where the string is an ISO month label and the list is the output of
            :func:`client.get_month_categories`.

    Returns:
        Dict mapping category name to a chronological list of
        ``{"month": label, "amount": spending_in_euros}`` dicts.

    Examples:
        >>> cats = [{"id": "c1", "name": "AWS", "budgeted": 0, "activity": -100000, "balance": 0}]
        >>> spending_trends([("2026-01", cats)])["AWS"]
        [{'month': '2026-01', 'amount': 100.0}]
    """
    trends: dict[str, list[dict[str, Any]]] = {}
    for month_label, categories in months_data:
        for cat in categories:
            name = cat.get("name", "")
            if not name:
                continue
            amount = client.milliunit_to_amount(abs(cat.get("activity", 0)))
            if name not in trends:
                trends[name] = []
            trends[name].append({"month": month_label, "amount": amount})
    return trends


def top_payees(
    transactions: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Aggregate transactions by payee and return the top spenders.

    Args:
        transactions: List of YNAB transaction dicts with ``payee_name``
            and ``amount`` fields (amounts are in milliunits, negative = expense).
        limit: Maximum number of payees to return (default 10).

    Returns:
        List of dicts ordered by total spending (descending):

        - ``payee_name`` — name of the payee
        - ``total`` — total amount spent in euros (positive)
        - ``count`` — number of transactions

    Examples:
        >>> txs = [
        ...     {"payee_name": "AWS", "amount": -50000},
        ...     {"payee_name": "AWS", "amount": -30000},
        ...     {"payee_name": "Loyer", "amount": -500000},
        ... ]
        >>> top_payees(txs, limit=1)[0]["payee_name"]
        'Loyer'
    """
    totals: dict[str, dict[str, Any]] = {}
    for tx in transactions:
        payee = tx.get("payee_name") or "Unknown"
        amount_mu = tx.get("amount", 0)
        if payee not in totals:
            totals[payee] = {"total_mu": 0, "count": 0}
        totals[payee]["total_mu"] += abs(amount_mu)
        totals[payee]["count"] += 1

    sorted_payees = sorted(totals.items(), key=lambda kv: kv[1]["total_mu"], reverse=True)
    return [
        {
            "payee_name": name,
            "total": client.milliunit_to_amount(data["total_mu"]),
            "count": data["count"],
        }
        for name, data in sorted_payees[:limit]
    ]
