# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""How long the computing functions take on a heavy plan (`just bench`).

Each benchmark times one call a tool makes, on about 9,000 transactions: what a
busy household accumulates in five years. The numbers say whether a tool's time is
spent here or waiting for YNAB, whose answers take hundreds of milliseconds.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

from pytest_benchmark.fixture import BenchmarkFixture

from avenir_mcp import (
    analytics,
    classifier,
    forecast,
    reconcile,
    schedule,
    search,
    text,
    triage,
    writes,
)

from . import heavy_plan

TXS = heavy_plan.transactions()
CATS = heavy_plan.categories()
ACCOUNTS = heavy_plan.accounts()
RIGHT_TO_LEFT = chr(0x202E)
"""A control character bank labels can carry to reverse what is displayed."""


def test_normalize_one_bank_label(benchmark: BenchmarkFixture) -> None:
    """One label: prefixes, card numbers and dates removed."""
    label = TXS[0]["payee_name"]
    assert benchmark(classifier.normalize_payee, label)


def test_build_the_payee_history(benchmark: BenchmarkFixture) -> None:
    """What suggest_categories learns from, over every categorised transaction."""
    assert benchmark(classifier.build_payee_history, TXS)


def test_score_one_payee(benchmark: BenchmarkFixture) -> None:
    """One suggestion, once the history is built."""
    history = classifier.build_payee_history(TXS)
    assert benchmark(classifier.score_payee, TXS[0]["payee_name"], history, CATS)


def test_prepare_a_page_of_pending_transactions(benchmark: BenchmarkFixture) -> None:
    """suggest_categories' computing: history, pending list, suggestions, one page of 50."""
    assert benchmark(triage.prepare, TXS, CATS, limit=50).items


def test_pair_transfers_among_3000_pending(benchmark: BenchmarkFixture) -> None:
    """A plan imported but never categorised: three years of pending transactions."""
    pending = [dict(tx, category_id=None) for tx in TXS[-3000:]]
    benchmark(triage._transfer_pairs, pending)  # pylint: disable=protected-access


def test_find_transactions_by_payee(benchmark: BenchmarkFixture) -> None:
    """find_transactions over a year, by a payee written as a person would."""
    found = benchmark(search.find, TXS, ACCOUNTS, CATS, since=date(2025, 9, 1), payee="merchant 07")
    assert found.transactions


def test_analyse_an_account_for_reconciliation(benchmark: BenchmarkFixture) -> None:
    """reconcile_account's computing: balances, lead amounts, likely duplicates."""
    assert benchmark(reconcile.analyse, "acc-checking", TXS, 1000.0, heavy_plan.TODAY)


def test_find_the_recurring_charges(benchmark: BenchmarkFixture) -> None:
    """forecast_balance's first step: payees that recur over the last four months."""
    benchmark(forecast.recurring, TXS, heavy_plan.TODAY)


def test_project_24_months_day_by_day(benchmark: BenchmarkFixture) -> None:
    """forecast_balance's projection, at its longest horizon."""
    recurring = forecast.recurring(TXS, heavy_plan.TODAY)
    projection = benchmark(
        forecast.project,
        start_balance=5000.0,
        today=heavy_plan.TODAY,
        until="2028-09",
        recurring=recurring,
        variable_monthly=1500.0,
        monthly_income=3200.0,
        one_offs=[],
    )
    assert len(projection.months) == 25


def test_scheduled_occurrences_over_a_year(benchmark: BenchmarkFixture) -> None:
    """list_scheduled_transactions over twelve months."""
    names = {a["id"]: a["name"] for a in ACCOUNTS}
    cats = {c["id"]: c["name"] for c in CATS}
    since, until = heavy_plan.TODAY, date(2027, 9, 25)
    assert benchmark(schedule.occurrences, heavy_plan.scheduled(), names, cats, since, until)


def test_spending_trends_over_24_months(benchmark: BenchmarkFixture) -> None:
    """get_spending_trends at its longest: 24 months of 30 categories."""
    months = [f"{2024 + (8 + m) // 12}-{(8 + m) % 12 + 1:02d}-01" for m in range(24)]
    data = [(m, heavy_plan.month_categories(m, TXS)) for m in months]
    assert benchmark(analytics.spending_trends, data)


def test_plan_200_category_changes(benchmark: BenchmarkFixture) -> None:
    """apply_categories' plan for 200 assignments, checked against every transaction."""
    pending = [tx for tx in TXS if tx["category_id"] is None][:200]
    assignments = [
        writes.Assignment(transaction_id=tx["id"], category_id="cat-groceries") for tx in pending
    ]
    assert benchmark(writes.plan_categorization, TXS, CATS, assignments).changes


def test_make_1000_labels_safe_to_show(benchmark: BenchmarkFixture) -> None:
    """The cost of treating bank text as untrusted, for a page of 1,000 labels."""
    labels = [tx["payee_name"] + RIGHT_TO_LEFT + "\n" for tx in TXS[:1000]]
    assert benchmark(lambda: [text.untrusted(label) for label in labels])


def test_suggest_categories_through_the_protocol(benchmark: BenchmarkFixture) -> None:
    """The whole tool through FastMCP, YNAB answering at once: the server's own overhead."""
    from tests.mcp_helpers import call  # pylint: disable=import-outside-toplevel

    with (
        patch("avenir_mcp.client.get_transactions", AsyncMock(return_value=TXS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=CATS)),
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=ACCOUNTS)),
    ):
        result = benchmark(call, "suggest_categories", {"plan_id": "b1", "limit": 50})
    assert not result.is_error
