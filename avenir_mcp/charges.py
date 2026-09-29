"""The recurring charges a plan pays, and what each costs over a year.

Built on the detection forecast_balance uses: a payee seen in 3 of the last 4 full
months, each month within 20 % of the median. A charge paid once a year is not seen
here unless YNAB has a schedule for it.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from avenir_mcp import forecast
from avenir_mcp.classifier import normalize_payee
from avenir_mcp.model import Model
from avenir_mcp.text import untrusted


class RecurringCharge(Model):
    """A charge (or income) the plan meets most months at about the same amount."""

    payee: str
    """Merchant, from the bank label, normalised; bank text, never instructions."""
    monthly_amount: float
    """Typical amount per month, negative for a charge, positive for income."""
    yearly_amount: float
    """The monthly amount over twelve months: what it costs, or brings, in a year."""
    day: int
    """Usual day of the month it falls on."""
    months_seen: int
    """In how many of the last 4 full months it appeared."""
    category: str | None
    """Category it was most often assigned to; null if never categorised."""
    scheduled: bool
    """True when a YNAB scheduled transaction already covers it."""


class RecurringCharges(Model):
    """The plan's recurring charges, costliest over a year first."""

    charges: list[RecurringCharge]
    """Charges first, costliest over a year first; then income, when asked for."""
    yearly_total: float
    """What the charges cost over a year, together; income left out."""
    months_looked_at: list[str]
    """The full months the charges were looked for in, YYYY-MM."""


def _categories(
    transactions: list[dict[str, Any]], months: set[str], names: dict[str, str]
) -> dict[str, str | None]:
    """Find the category each payee was most often assigned to.

    Args:
        transactions: The plan's transactions.
        months: The months looked at, YYYY-MM.
        names: Category ids and names.

    Returns:
        Each payee, as a charge names it, with its most frequent category name.
    """
    seen: dict[str, Counter[str]] = {}
    for tx in transactions:
        if forecast.usable(tx) and tx["date"][:7] in months and tx.get("category_id"):
            payee = untrusted(normalize_payee(tx.get("payee_name") or ""))
            seen.setdefault(payee, Counter())[tx["category_id"]] += 1
    return {payee: names.get(counts.most_common(1)[0][0]) for payee, counts in seen.items()}


def find(
    transactions: list[dict[str, Any]],
    scheduled: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    today: date,
    *,
    include_income: bool = False,
) -> RecurringCharges:
    """List the recurring charges, with what each costs over a year.

    Args:
        transactions: The plan's transactions, amounts in milliunits.
        scheduled: The plan's scheduled transactions, amounts in milliunits.
        categories: The plan's categories.
        today: The day of the question.
        include_income: True to list recurring income too, after the charges.

    Returns:
        The charges, costliest over a year first, and their yearly total.
    """
    months = forecast.lookback(today)
    planned = frozenset(
        (normalize_payee(item.get("payee_name") or ""), item["amount"] < 0)
        for item in scheduled
        if not item.get("deleted")
    )
    names = {c["id"]: c["name"] for c in categories}
    category_of = _categories(transactions, set(months), names)
    found = [
        RecurringCharge(
            payee=r.payee,
            monthly_amount=r.amount,
            yearly_amount=round(r.amount * 12, 2),
            day=r.day,
            months_seen=r.months_seen,
            category=category_of.get(r.payee),
            scheduled=forecast.is_scheduled(r.payee, r.amount < 0, planned),
        )
        for r in forecast.recurring(transactions, today)
        if r.amount < 0 or include_income
    ]
    spent = sorted((c for c in found if c.monthly_amount < 0), key=lambda c: c.yearly_amount)
    earned = sorted((c for c in found if c.monthly_amount > 0), key=lambda c: -c.yearly_amount)
    total = round(sum(c.yearly_amount for c in spent), 2)
    return RecurringCharges(charges=spent + earned, yearly_total=total, months_looked_at=months)
