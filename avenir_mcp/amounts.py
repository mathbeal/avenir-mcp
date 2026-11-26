# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Amounts an agent may pass: finite, and within what a household budget can hold."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from pydantic import Field

MAX_AMOUNT = 1_000_000_000

Amount = Annotated[
    float,
    Field(
        allow_inf_nan=False,
        ge=-MAX_AMOUNT,
        le=MAX_AMOUNT,
        description="In currency units, negative for money out; at most a billion either way.",
    ),
]
"""An amount in currency units, checked by the tool's argument schema before any call."""

DEFAULT_CURRENCY_FORMAT: dict[str, Any] = {"decimal_digits": 2}
"""YNAB's own fallback, used when a plan's currency_format is unavailable (null)."""


def decimal_places(amount: float) -> int:
    """How many decimal digits amount needs, written as the shortest string that is it.

    Python's float repr is the shortest decimal that round-trips to the same float, so
    this reads the digits the caller wrote, not noise from the binary representation
    (0.1 has one decimal place, not sixteen).

    Args:
        amount: A finite amount in currency units.

    Returns:
        0 for a whole number, otherwise how many digits follow its decimal point.
    """
    exponent = Decimal(str(amount)).normalize().as_tuple().exponent
    return max(0, -exponent) if isinstance(exponent, int) else 0


def format_amount(
    amount: float, currency_format: dict[str, Any] | None = None, *, signed: bool = False
) -> str:
    """Format an amount with exactly the decimal digits the plan's currency uses.

    The one formatter for every amount a tool shows the user: previews, questions and
    error messages all go through it, instead of a hardcoded two decimal places.

    Args:
        amount: An amount in currency units.
        currency_format: The plan's currency format; omit for DEFAULT_CURRENCY_FORMAT.
        signed: Prefix a positive amount with '+'; a negative one already has its '-'.
            An amount that rounds to zero at this precision is shown as '0.00' (or
            however many digits), never '+0.00' or '-0.00': zero has no direction.

    Returns:
        The amount, formatted to the currency's decimal digits.
    """
    digits = (currency_format or DEFAULT_CURRENCY_FORMAT)["decimal_digits"]
    if signed and round(amount, digits) == 0:
        return f"{0:.{digits}f}"
    return f"{amount:{'+' if signed else ''}.{digits}f}"
