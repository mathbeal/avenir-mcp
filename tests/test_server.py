"""Tests for server.py — FastMCP instance and all 14 MCP tools."""

# pylint: disable=redefined-outer-name

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from avenir_mcp import server

# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------


def test_mcp_instance_name() -> None:
    """The FastMCP instance must be named 'avenir'."""
    assert server.mcp.name == "avenir"


def test_tools_registered() -> None:
    """All 8 tools must be registered on the FastMCP instance."""
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    expected = [
        "list_budgets",
        "get_category_balances",
        "get_monthly_summary",
        "get_budget_vs_actual",
        "get_spending_trends",
        "get_uncategorized_transactions",
        "suggest_category",
        "classify_transaction",
    ]
    for name in expected:
        assert name in tool_names


# ---------------------------------------------------------------------------
# list_budgets
# ---------------------------------------------------------------------------


def test_list_budgets_delegates_to_client() -> None:
    """list_budgets should return whatever client.get_budgets() returns."""
    budgets = [{"id": "b1", "name": "Business"}]
    with patch("avenir_mcp.client.get_budgets", new=AsyncMock(return_value=budgets)):
        result = asyncio.run(server.list_budgets())
    assert result == budgets


# ---------------------------------------------------------------------------
# get_category_balances
# ---------------------------------------------------------------------------


def test_get_category_balances_default_month() -> None:
    """Default month is 'current'."""
    cats = [{"id": "c1", "name": "Rent", "budgeted": 500_000, "activity": 0, "balance": 500_000}]
    with patch(
        "avenir_mcp.client.get_month_categories", new=AsyncMock(return_value=cats)
    ) as mock_fn:
        asyncio.run(server.get_category_balances("b1"))
    mock_fn.assert_called_once_with("b1", "current")


def test_get_category_balances_explicit_month() -> None:
    """Explicit month is forwarded to client.get_month_categories."""
    cats: list[dict[str, Any]] = []
    with patch(
        "avenir_mcp.client.get_month_categories", new=AsyncMock(return_value=cats)
    ) as mock_fn:
        asyncio.run(server.get_category_balances("b1", "2026-03-01"))
    mock_fn.assert_called_once_with("b1", "2026-03-01")


# ---------------------------------------------------------------------------
# get_monthly_summary
# ---------------------------------------------------------------------------


def test_get_monthly_summary_delegates_to_client() -> None:
    """get_monthly_summary should return whatever client.get_month() returns."""
    month = {"month": "2026-04-01", "budgeted": 5_000_000, "activity": -3_200_000}
    with patch("avenir_mcp.client.get_month", new=AsyncMock(return_value=month)):
        result = asyncio.run(server.get_monthly_summary("b1", "2026-04-01"))
    assert result["month"] == "2026-04-01"


# ---------------------------------------------------------------------------
# get_budget_vs_actual
# ---------------------------------------------------------------------------


def test_get_budget_vs_actual_returns_analytics_output() -> None:
    """get_budget_vs_actual should chain get_month_categories and analytics."""
    cats = [
        {"id": "c1", "name": "Rent", "budgeted": 500_000, "activity": -400_000, "balance": 100_000}
    ]
    with patch("avenir_mcp.client.get_month_categories", new=AsyncMock(return_value=cats)):
        result = asyncio.run(server.get_budget_vs_actual("b1"))
    assert result[0]["utilization_pct"] == 80.0


# ---------------------------------------------------------------------------
# get_spending_trends
# ---------------------------------------------------------------------------


def test_get_spending_trends_fetches_last_n_months() -> None:
    """get_spending_trends with months_count=2 should fetch 2 months of categories."""
    months = [{"month": "2026-02-01"}, {"month": "2026-03-01"}, {"month": "2026-04-01"}]
    cats = [{"id": "c1", "name": "AWS", "budgeted": 0, "activity": -100_000, "balance": 0}]

    mock_get_months = AsyncMock(return_value=months)
    mock_month_cats = AsyncMock(return_value=cats)

    with (
        patch("avenir_mcp.client.get_months", mock_get_months),
        patch("avenir_mcp.client.get_month_categories", mock_month_cats),
    ):
        result = asyncio.run(server.get_spending_trends("b1", months_count=2))

    # Should have fetched categories for exactly 2 months (last 2)
    assert mock_month_cats.call_count == 2
    assert "AWS" in result


# ---------------------------------------------------------------------------
# get_uncategorized_transactions
# ---------------------------------------------------------------------------


def test_get_uncategorized_transactions_delegates_to_client() -> None:
    """get_uncategorized_transactions should call get_transactions with uncategorized_only=True."""
    txs = [{"id": "t1", "payee_name": "NewVendor", "category_id": None}]
    with patch("avenir_mcp.client.get_transactions", new=AsyncMock(return_value=txs)) as mock_fn:
        result = asyncio.run(server.get_uncategorized_transactions("b1"))
    mock_fn.assert_called_once_with("b1", uncategorized_only=True)
    assert result == txs


# ---------------------------------------------------------------------------
# suggest_category
# ---------------------------------------------------------------------------


def test_suggest_category_high_confidence_auto_classify() -> None:
    """suggest_category returns auto_classify=True when confidence ≥ threshold."""
    tx = {"id": "t1", "payee_name": "AWS", "category_id": None}
    all_txs = [
        {"payee_name": "AWS", "category_id": "c1"},
        {"payee_name": "AWS", "category_id": "c1"},
        {"payee_name": "AWS", "category_id": "c1"},
    ]
    categories = [{"id": "c1", "name": "AWS / Cloud"}]

    with (
        patch("avenir_mcp.client.get_transaction", new=AsyncMock(return_value=tx)),
        patch("avenir_mcp.client.get_transactions", new=AsyncMock(return_value=all_txs)),
        patch("avenir_mcp.client.get_categories", new=AsyncMock(return_value=categories)),
    ):
        result = asyncio.run(server.suggest_category("b1", "t1"))

    assert result["auto_classify"] is True
    assert result["category_id"] == "c1"


def test_suggest_category_low_confidence_returns_candidates() -> None:
    """suggest_category returns candidates when confidence < threshold."""
    tx = {"id": "t1", "payee_name": "AWS", "category_id": None}
    all_txs = [
        {"payee_name": "AWS", "category_id": "c1"},
        {"payee_name": "AWS", "category_id": "c2"},
    ]
    categories = [{"id": "c1", "name": "Cat1"}, {"id": "c2", "name": "Cat2"}]

    with (
        patch("avenir_mcp.client.get_transaction", new=AsyncMock(return_value=tx)),
        patch("avenir_mcp.client.get_transactions", new=AsyncMock(return_value=all_txs)),
        patch("avenir_mcp.client.get_categories", new=AsyncMock(return_value=categories)),
    ):
        result = asyncio.run(server.suggest_category("b1", "t1"))

    assert result["auto_classify"] is False
    assert "candidates" in result


# ---------------------------------------------------------------------------
# classify_transaction
# ---------------------------------------------------------------------------


def test_classify_transaction_calls_patch() -> None:
    """classify_transaction must call client.patch_transaction with correct args."""
    updated_tx = {"id": "t1", "category_id": "c99"}
    with patch(
        "avenir_mcp.client.patch_transaction", new=AsyncMock(return_value=updated_tx)
    ) as mock_fn:
        result = asyncio.run(server.classify_transaction("b1", "t1", "c99"))
    mock_fn.assert_called_once_with("b1", "t1", "c99")
    assert result["category_id"] == "c99"


# ---------------------------------------------------------------------------
# list_category_groups / create_category
# ---------------------------------------------------------------------------


def test_list_category_groups_delegates_to_client() -> None:
    """list_category_groups must return client.get_category_groups output."""
    groups = [{"id": "g1", "name": "Software"}]
    with patch(
        "avenir_mcp.client.get_category_groups", new=AsyncMock(return_value=groups)
    ) as mock_fn:
        result = asyncio.run(server.list_category_groups("b1"))
    mock_fn.assert_called_once_with("b1")
    assert result == groups


def test_create_category_delegates_to_client() -> None:
    """create_category must call client.create_category with correct args."""
    created = {"id": "c42", "name": "Miscellaneous"}
    with patch("avenir_mcp.client.create_category", new=AsyncMock(return_value=created)) as mock_fn:
        result = asyncio.run(server.create_category("b1", "g1", "Miscellaneous"))
    mock_fn.assert_called_once_with("b1", "g1", "Miscellaneous")
    assert result == created


def test_new_category_tools_registered() -> None:
    """The category-management tools must be exposed over MCP."""
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert "list_category_groups" in tool_names
    assert "create_category" in tool_names


# ---------------------------------------------------------------------------
# set_category_budget / list_accounts
# ---------------------------------------------------------------------------


def test_set_category_budget_delegates_to_client() -> None:
    """set_category_budget must call client.set_category_budgeted with correct args."""
    updated = {"id": "c1", "budgeted": 1890000}
    with patch(
        "avenir_mcp.client.set_category_budgeted", new=AsyncMock(return_value=updated)
    ) as mock_fn:
        result = asyncio.run(server.set_category_budget("b1", "2026-09-01", "c1", 1890.0))
    mock_fn.assert_called_once_with("b1", "2026-09-01", "c1", 1890.0)
    assert result == updated


def test_list_accounts_delegates_to_client() -> None:
    """list_accounts must return client.get_accounts output."""
    accounts = [{"id": "a1", "name": "Checking", "balance": 1250.0}]
    with patch("avenir_mcp.client.get_accounts", new=AsyncMock(return_value=accounts)) as mock_fn:
        result = asyncio.run(server.list_accounts("b1"))
    mock_fn.assert_called_once_with("b1")
    assert result == accounts


def test_budget_tools_registered() -> None:
    """The budgeting and account tools must be exposed over MCP."""
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert "set_category_budget" in tool_names
    assert "list_accounts" in tool_names


def test_create_transactions_delegates_to_client() -> None:
    """create_transactions must call client.create_transactions with correct args."""
    items = [{"date": "2026-07-01", "amount": -16.0, "payee_name": "X"}]
    summary = {"created": 1, "transaction_ids": ["t1"], "duplicate_import_ids": []}
    with patch(
        "avenir_mcp.client.create_transactions", new=AsyncMock(return_value=summary)
    ) as mock_fn:
        result = asyncio.run(server.create_transactions("b1", "a1", items))
    mock_fn.assert_called_once_with("b1", "a1", items)
    assert result == summary
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert "create_transactions" in tool_names


def test_approve_transactions_delegates_to_client() -> None:
    """approve_transactions must call client.approve_transactions and be exposed."""
    with patch(
        "avenir_mcp.client.approve_transactions", new=AsyncMock(return_value={"approved": 1})
    ) as mock_fn:
        result = asyncio.run(server.approve_transactions("b1", ["t1"]))
    mock_fn.assert_called_once_with("b1", ["t1"])
    assert result == {"approved": 1}
    assert "approve_transactions" in [t.name for t in asyncio.run(server.mcp.list_tools())]


# ---------------------------------------------------------------------------
# main — entry point of the `avenir-mcp` command
# ---------------------------------------------------------------------------


def test_main_runs_stdio_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without configuration, the server speaks stdio, as MCP clients expect."""
    monkeypatch.delenv("AVENIR_MCP_TRANSPORT", raising=False)
    with patch.object(server.mcp, "run") as run:
        server.main()
    run.assert_called_once_with(transport="stdio")


def test_main_runs_http_on_localhost_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_TRANSPORT=http alone serves on 127.0.0.1:8103, never on all interfaces."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.delenv("AVENIR_MCP_HOST", raising=False)
    monkeypatch.delenv("AVENIR_MCP_PORT", raising=False)
    monkeypatch.setenv("HOST", "my-laptop.local")  # zsh sets HOST; it must be ignored
    with patch.object(server.mcp, "run") as run:
        server.main()
    run.assert_called_once_with(transport="streamable-http", host="127.0.0.1", port=8103)


def test_main_runs_http_on_configured_host_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_HOST and AVENIR_MCP_PORT choose the HTTP address."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.setenv("AVENIR_MCP_HOST", "127.0.0.2")
    monkeypatch.setenv("AVENIR_MCP_PORT", "9000")
    with patch.object(server.mcp, "run") as run:
        server.main()
    run.assert_called_once_with(transport="streamable-http", host="127.0.0.2", port=9000)


def test_today_is_the_real_date() -> None:
    """Tools reckon from the actual date unless a test fixes it."""
    assert server.today() == date.today()
