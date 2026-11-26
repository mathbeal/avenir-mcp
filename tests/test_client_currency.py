# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""A plan's currency format: read from YNAB, and used to check amounts before sending them."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from avenir_mcp import amounts, client

EUR = {"decimal_digits": 2}
BHD = {"decimal_digits": 3}
JPY = {"decimal_digits": 0}

# The real implementation, captured before conftest's autouse fixture patches the name
# `client.get_currency_format` for every other test in the suite.
_get_currency_format = client.get_currency_format


def test_currency_format_is_read_from_the_plan_settings() -> None:
    """One GET on the plan's settings; the currency_format is returned as is."""
    settings = {"date_format": {"format": "DD/MM/YYYY"}, "currency_format": BHD}
    get = AsyncMock(return_value={"data": {"settings": settings}})
    with patch("avenir_mcp.client._get", get):
        found = asyncio.run(_get_currency_format("b1"))
    assert found == BHD
    assert get.call_args.args == ("/plans/b1/settings",)


def test_currency_format_defaults_to_two_decimal_digits_when_ynab_has_none() -> None:
    """YNAB documents currency_format as nullable: avenir-mcp falls back to its own default."""
    settings = {"date_format": {"format": "DD/MM/YYYY"}, "currency_format": None}
    get = AsyncMock(return_value={"data": {"settings": settings}})
    with patch("avenir_mcp.client._get", get):
        found = asyncio.run(_get_currency_format("b1"))
    assert found == amounts.DEFAULT_CURRENCY_FORMAT
    assert found["decimal_digits"] == 2


@pytest.mark.parametrize(
    ("amount", "currency_format"),
    [
        (80.004, EUR),  # a thousandth, EUR holds only cents
        (0.004, EUR),  # same, smaller
        (0.0004, BHD),  # a ten-thousandth, no YNAB currency holds that
        (1.5, JPY),  # half a yen
    ],
)
def test_amount_to_milliunit_refuses_what_the_currency_cannot_hold(
    amount: float, currency_format: dict[str, int]
) -> None:
    """An amount with more decimal digits than the currency uses is refused, not rounded away."""
    with pytest.raises(ValueError, match="decimal digit"):
        client.amount_to_milliunit(amount, currency_format)


@pytest.mark.parametrize(
    ("amount", "currency_format", "milliunit"),
    [
        (111.32, EUR, 111320),
        (1.239, BHD, 1239),
        (80.0, JPY, 80000),
        (0.004, BHD, 4),
    ],
)
def test_amount_to_milliunit_accepts_what_the_currency_holds_exactly(
    amount: float, currency_format: dict[str, int], milliunit: int
) -> None:
    """A whole number of the currency's smallest unit converts exactly, whatever its precision."""
    assert client.amount_to_milliunit(amount, currency_format) == milliunit


def test_amount_to_milliunit_without_a_currency_format_is_unchecked() -> None:
    """Callers with no plan currency in hand (forecasts, payoff) are not newly restricted."""
    assert client.amount_to_milliunit(80.004) == 80004
