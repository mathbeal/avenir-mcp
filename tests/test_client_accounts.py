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
