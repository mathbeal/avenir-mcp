# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for amounts.py — amounts an agent may pass, refused when impossible."""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import TypeAdapter, ValidationError

from avenir_mcp import amounts, client

from .mcp_helpers import call

AMOUNT: TypeAdapter[float] = TypeAdapter(amounts.Amount)
TOO_LARGE = amounts.MAX_AMOUNT * 10


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, TOO_LARGE, -TOO_LARGE])
def test_impossible_amounts_are_refused(value: float) -> None:
    """Not a number, infinity or beyond a billion: refused before anything happens."""
    with pytest.raises(ValidationError):
        AMOUNT.validate_python(value)


def test_ordinary_amounts_pass() -> None:
    """Everyday amounts, and the limit itself, are accepted."""
    assert AMOUNT.validate_python(-12.5) == -12.5
    assert AMOUNT.validate_python(amounts.MAX_AMOUNT) == amounts.MAX_AMOUNT


def test_conversion_refuses_what_is_not_finite() -> None:
    """Even called directly, the conversion never sends a non-number to YNAB."""
    with pytest.raises(ValueError, match="finite"):
        client.amount_to_milliunit(math.nan)


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("set_category_budget", {"month": "2026-09-01", "category_id": "c", "amount": TOO_LARGE}),
        ("reconcile_account", {"account_id": "acc", "bank_balance": TOO_LARGE}),
        ("forecast_balance", {"until": "2026-12", "monthly_income": TOO_LARGE}),
        (
            "forecast_balance",
            {
                "until": "2026-12",
                "one_offs": [{"date": "2026-10-01", "amount": -TOO_LARGE, "label": "x"}],
            },
        ),
        (
            "create_transactions",
            {
                "account_id": "acc",
                "transactions": [{"date": "2026-09-01", "amount": TOO_LARGE, "payee_name": "X"}],
            },
        ),
    ],
)
def test_tools_refuse_impossible_amounts_without_calling_ynab(
    tool: str, args: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The argument schema stops the call: YNAB is never asked."""
    monkeypatch.setenv("AVENIR_MCP_WRITE", "1")
    with patch("avenir_mcp.client._get", AsyncMock()) as get:
        result = call(tool, {"plan_id": "b1", **args})
    assert result.is_error
    assert "less than or equal" in str(result.content) or "greater than or equal" in str(
        result.content
    )
    get.assert_not_awaited()
