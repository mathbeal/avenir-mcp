"""Tests for analytics.py — budget/actual, trends, top payees."""

from __future__ import annotations

from typing import Any

from avenir_mcp import analytics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cat(
    cat_id: str,
    name: str,
    budgeted: int = 0,
    activity: int = 0,
    balance: int = 0,
) -> dict[str, Any]:
    return {
        "id": cat_id,
        "name": name,
        "budgeted": budgeted,
        "activity": activity,
        "balance": balance,
    }


def _tx(payee: str, amount: int) -> dict[str, Any]:
    return {"payee_name": payee, "amount": amount}


# ---------------------------------------------------------------------------
# budget_vs_actual
# ---------------------------------------------------------------------------


def test_budget_vs_actual_utilization() -> None:
    """400€ actual on 500€ budget → utilization_pct=80.0."""
    cats = [_cat("c1", "Rent", budgeted=500_000, activity=-400_000, balance=100_000)]
    result = analytics.budget_vs_actual(cats)
    assert result[0]["utilization_pct"] == 80.0
    assert result[0]["budgeted"] == 500.0
    assert result[0]["actual"] == 400.0
    assert result[0]["balance"] == 100.0


def test_budget_vs_actual_overspend() -> None:
    """Spending more than budget: activity > budgeted → utilization > 100."""
    cats = [_cat("c1", "AWS", budgeted=100_000, activity=-150_000, balance=-50_000)]
    result = analytics.budget_vs_actual(cats)
    assert result[0]["utilization_pct"] == 150.0
    assert result[0]["balance"] == -50.0


def test_budget_vs_actual_zero_budget_no_division() -> None:
    """Category with budgeted=0 must not cause a ZeroDivisionError."""
    cats = [_cat("c1", "Misc", budgeted=0, activity=-20_000, balance=0)]
    result = analytics.budget_vs_actual(cats)
    assert result[0]["utilization_pct"] == 0.0


def test_budget_vs_actual_preserves_all_categories() -> None:
    """All input categories should appear in the output."""
    cats = [
        _cat("c1", "Rent", budgeted=500_000, activity=-500_000),
        _cat("c2", "AWS", budgeted=200_000, activity=-80_000),
    ]
    result = analytics.budget_vs_actual(cats)
    assert len(result) == 2


def test_budget_vs_actual_actual_is_always_positive() -> None:
    """The 'actual' field should always be positive (absolute value of activity)."""
    cats = [_cat("c1", "Rent", budgeted=500_000, activity=-400_000)]
    result = analytics.budget_vs_actual(cats)
    assert result[0]["actual"] >= 0.0


def test_budget_vs_actual_doctest() -> None:
    """Doctest example: 80.0% utilization."""
    cats = [
        {"id": "c1", "name": "Rent", "budgeted": 500_000, "activity": -400_000, "balance": 100_000}
    ]
    assert analytics.budget_vs_actual(cats)[0]["utilization_pct"] == 80.0


# ---------------------------------------------------------------------------
# spending_trends
# ---------------------------------------------------------------------------


def test_spending_trends_has_all_months() -> None:
    """Each category should have one entry per month in the input."""
    cats_jan = [_cat("c1", "AWS", activity=-100_000)]
    cats_feb = [_cat("c1", "AWS", activity=-120_000)]
    data = [("2026-01", cats_jan), ("2026-02", cats_feb)]
    result = analytics.spending_trends(data)
    assert len(result["AWS"]) == 2


def test_spending_trends_amounts_in_euros() -> None:
    """Amounts should be converted from milliunits to euros."""
    cats = [_cat("c1", "AWS", activity=-250_000)]
    result = analytics.spending_trends([("2026-04", cats)])
    assert result["AWS"][0]["amount"] == 250.0


def test_spending_trends_doctest() -> None:
    """Doctest example from analytics.spending_trends."""
    data = [
        (
            "2026-01",
            [{"id": "c1", "name": "AWS", "budgeted": 0, "activity": -100_000, "balance": 0}],
        )
    ]
    assert analytics.spending_trends(data)["AWS"] == [{"month": "2026-01", "amount": 100.0}]


def test_spending_trends_skips_categories_with_empty_name() -> None:
    """Categories without a name should be silently ignored."""
    cats = [{"id": "c1", "name": "", "budgeted": 0, "activity": -10_000, "balance": 0}]
    result = analytics.spending_trends([("2026-04", cats)])
    assert not result


# ---------------------------------------------------------------------------
# top_payees
# ---------------------------------------------------------------------------


def test_top_payees_ordered_by_total() -> None:
    """Payees should be sorted by total spending, descending."""
    txs = [_tx("AWS", -50_000), _tx("AWS", -30_000), _tx("Rent", -500_000)]
    result = analytics.top_payees(txs)
    assert result[0]["payee_name"] == "Rent"
    assert result[1]["payee_name"] == "AWS"


def test_top_payees_limit_respected() -> None:
    """Result must not exceed the requested limit."""
    txs = [_tx(f"Vendor{i}", -(i + 1) * 10_000) for i in range(20)]
    result = analytics.top_payees(txs, limit=5)
    assert len(result) == 5


def test_top_payees_total_in_euros() -> None:
    """Total spending should be in euros, not milliunits."""
    txs = [_tx("AWS", -50_000), _tx("AWS", -50_000)]
    result = analytics.top_payees(txs)
    assert result[0]["total"] == 100.0


def test_top_payees_count_is_transaction_count() -> None:
    """Count should reflect the number of transactions for that payee."""
    txs = [_tx("AWS", -10_000), _tx("AWS", -20_000), _tx("AWS", -30_000)]
    result = analytics.top_payees(txs)
    assert result[0]["count"] == 3


def test_top_payees_empty_transactions() -> None:
    """An empty transaction list should return an empty result."""
    assert analytics.top_payees([]) == []


def test_top_payees_null_payee_name_grouped_as_unknown() -> None:
    """Transactions with no payee name should be grouped under 'Unknown'."""
    txs = [{"payee_name": None, "amount": -10_000}]
    result = analytics.top_payees(txs)
    assert result[0]["payee_name"] == "Unknown"


def test_top_payees_doctest() -> None:
    """Doctest example: Rent is top payee."""
    txs = [
        {"payee_name": "AWS", "amount": -50_000},
        {"payee_name": "AWS", "amount": -30_000},
        {"payee_name": "Rent", "amount": -500_000},
    ]
    assert analytics.top_payees(txs, limit=1)[0]["payee_name"] == "Rent"
