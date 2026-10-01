# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""import_transactions through the MCP protocol: the bank's latest transactions, fetched."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

from .mcp_helpers import call


async def _never_asked(*_: Any) -> Any:
    raise AssertionError("import_transactions must not ask the user")


def test_imported_transactions_are_counted_and_listed() -> None:
    """The answer says how many came in, their ids, and what to do next."""
    with patch("avenir_mcp.client.import_transactions", AsyncMock(return_value=["t7", "t8"])):
        data = call("import_transactions", {"plan_id": "b1"}, _never_asked).structured_content
    assert data["imported"] == 2
    assert data["transaction_ids"] == ["t7", "t8"]
    assert "suggest_categories" in data["message"]


def test_nothing_new_says_so() -> None:
    """When the banks have nothing new, the answer says it plainly."""
    with patch("avenir_mcp.client.import_transactions", AsyncMock(return_value=[])):
        data = call("import_transactions", {"plan_id": "b1"}, _never_asked).structured_content
    assert data == {
        "imported": 0,
        "transaction_ids": [],
        "message": "No new transaction to import.",
    }
