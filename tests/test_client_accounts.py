# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""How get_accounts reports each account's bank link and last reconciliation."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from avenir_mcp import client


@pytest.mark.parametrize(
    ("fields", "link", "reconciled"),
    [
        ({"direct_import_linked": True, "direct_import_in_error": False}, "healthy", None),
        ({"direct_import_linked": True, "direct_import_in_error": True}, "broken", None),
        ({"direct_import_linked": False, "direct_import_in_error": False}, "none", None),
        ({}, "none", None),
        ({"last_reconciled_at": "2026-08-31T18:02:11.000Z"}, "none", "2026-08-31"),
        ({"last_reconciled_at": None}, "none", None),
    ],
)
def test_an_account_says_whether_its_bank_link_works_and_when_it_was_reconciled(
    fields: dict[str, Any], link: str, reconciled: str | None
) -> None:
    """The bank link is healthy, broken or absent; the last reconciliation is a date or None."""
    balances = dict.fromkeys(("balance", "cleared_balance", "uncleared_balance"), 0)
    account = {"id": "s1", "name": "Savings", "type": "savings", "on_budget": True} | balances
    account |= {"closed": False, "deleted": False, **fields}
    answer = AsyncMock(return_value={"data": {"accounts": [account]}})
    with patch("avenir_mcp.client._get", answer):
        [result] = asyncio.run(client.get_accounts("b1"))
    assert result["bank_link"] == link
    assert result["last_reconciled"] == reconciled


def test_debt_terms_come_in_percent_and_currency_units() -> None:
    """YNAB gives a loan's rates in thousandths of a percent and its payments in milliunits."""
    loan = {"id": "l1", "name": "Car loan", "type": "autoLoan", "on_budget": False}
    loan |= {"closed": False, "deleted": False, "balance": -4_250_500}
    loan |= {
        "debt_interest_rates": {"2025-04-01": 4_500, "2026-01-01": 3_375},
        "debt_minimum_payments": {"2025-04-01": 400_000},
        "debt_escrow_amounts": {"2025-04-01": 0},
    }
    card = {"id": "c1", "name": "Card", "type": "creditCard", "on_budget": True}
    card |= {"closed": False, "deleted": False, "balance": -120_000}
    card |= dict.fromkeys(("debt_interest_rates", "debt_minimum_payments", "debt_escrow_amounts"))
    gone = loan | {"id": "l0", "deleted": True}
    answer = AsyncMock(return_value={"data": {"accounts": [loan, card, gone]}})
    with patch("avenir_mcp.client._get", answer):
        found = asyncio.run(client.get_debt_terms("b1"))
    answer.assert_awaited_once_with("/plans/b1/accounts")
    assert found == [
        {
            "id": "l1",
            "name": "Car loan",
            "type": "autoLoan",
            "on_budget": False,
            "closed": False,
            "balance": -4_250.5,
            "interest_rates": {"2025-04-01": 4.5, "2026-01-01": 3.375},
            "minimum_payments": {"2025-04-01": 400.0},
            "escrow_amounts": {"2025-04-01": 0.0},
        },
        {
            "id": "c1",
            "name": "Card",
            "type": "creditCard",
            "on_budget": True,
            "closed": False,
            "balance": -120.0,
            "interest_rates": {},
            "minimum_payments": {},
            "escrow_amounts": {},
        },
    ]
