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


EUR = {"decimal_digits": 2}
BHD = {"decimal_digits": 3}
JPY = {"decimal_digits": 0}


@pytest.mark.parametrize(
    ("amount", "currency_format", "expected"),
    [
        (80.0, EUR, "80.00"),
        (80.0, BHD, "80.000"),
        (80.0, JPY, "80"),
        (-5.25, EUR, "-5.25"),
        (1.239, BHD, "1.239"),
        (80.0, None, "80.00"),
    ],
)
def test_format_amount_uses_the_currencys_decimal_digits(
    amount: float, currency_format: dict[str, int] | None, expected: str
) -> None:
    """Every amount shown to the user goes through this one formatter."""
    assert amounts.format_amount(amount, currency_format) == expected


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(150.0, "+150.00"), (-22.5, "-22.50"), (0.0, "0.00"), (0.001, "0.00"), (-0.001, "0.00")],
)
def test_format_amount_signed_marks_positive_and_collapses_a_rounding_zero(
    amount: float, expected: str
) -> None:
    """A category's available amount is signed so it is never read as the wrong direction."""
    assert amounts.format_amount(amount, EUR, signed=True) == expected


@pytest.mark.parametrize(
    ("amount", "places"),
    [(80.0, 0), (80.004, 3), (0.1, 1), (-5.25, 2), (1_200_000.0, 0), (0.0, 0)],
)
def test_decimal_places_reads_the_shortest_decimal_that_is_the_float(
    amount: float, places: int
) -> None:
    """Binary floating-point noise is not counted: 0.1 needs one place, not sixteen."""
    assert amounts.decimal_places(amount) == places


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
