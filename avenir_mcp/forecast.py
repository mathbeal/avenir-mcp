"""Project an account's balance month by month.

Three sources, each an assumption the caller can see and change: charges that
recur in the history, the average of everything else, and what the caller
expects (monthly income, one-off amounts). Sums are made in milliunits.
"""

from __future__ import annotations

import calendar
import statistics
from collections import defaultdict
from datetime import date
from typing import Any, TypedDict

from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp.classifier import normalize_payee
from avenir_mcp.client import amount_to_milliunit, milliunit_to_amount

LOOKBACK_MONTHS = 4
MIN_MONTHS_SEEN = 3
AMOUNT_TOLERANCE = 0.2
VARIABLE_MONTHS = 3


@with_config(ConfigDict(use_attribute_docstrings=True))
class Recurring(TypedDict):
    """A charge (or income) seen most months at about the same amount."""

    payee: str
    """Normalised payee name."""
    amount: float
    """Median monthly amount, negative for a charge, positive for income."""
    day: int
    """Median day of the month it falls on."""
    months_seen: int
    """How many of the last 4 full months it appeared in."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class OneOff(TypedDict):
    """An amount expected once, on a date."""

    date: str
    """Day it is expected, YYYY-MM-DD."""
    amount: float
    """Amount, negative for a payment, positive for money received."""
    label: str
    """What it is, for the reader."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class MonthProjection(TypedDict):
    """One projected month."""

    month: str
    """Month, YYYY-MM."""
    start: float
    """Projected balance on the first day (today's balance for the current month)."""
    inflows: float
    """Money expected in during the month."""
    outflows: float
    """Money expected out during the month, negative."""
    end: float
    """Projected balance at the end of the month."""
    lowest: float
    """Lowest projected balance within the month, day by day."""


@with_config(ConfigDict(use_attribute_docstrings=True))
class Projection(TypedDict):
    """The projected months and the first one where money runs out."""

    months: list[MonthProjection]
    """One projection per month, from the current month to the horizon."""
    first_shortfall: str | None
    """First month whose lowest balance is below zero; null if none."""


def _months_before(today: date, count: int) -> list[str]:
    """The `count` full months before today's month, oldest first."""
    year, month = today.year, today.month
    months = []
    for _ in range(count):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        months.append(f"{year:04d}-{month:02d}")
    return sorted(months)


def _usable(tx: dict[str, Any]) -> bool:
    return not tx.get("deleted") and not tx.get("transfer_account_id")


def recurring(transactions: list[dict[str, Any]], today: date) -> list[Recurring]:
    """Payees seen in 3 of the last 4 full months, each month within 20 % of the median."""
    months = set(_months_before(today, LOOKBACK_MONTHS))
    groups: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        if _usable(tx) and tx["date"][:7] in months:
            payee = normalize_payee(tx.get("payee_name") or "")
            if payee:
                groups[(payee, tx["amount"] < 0)].append(tx)
    found: list[Recurring] = []
    for (payee, _), txs in sorted(groups.items()):
        per_month: dict[str, int] = defaultdict(int)
        for tx in txs:
            per_month[tx["date"][:7]] += tx["amount"]
        if len(per_month) < MIN_MONTHS_SEEN:
            continue
        median = statistics.median(per_month.values())
        if all(abs(v - median) <= abs(median) * AMOUNT_TOLERANCE for v in per_month.values()):
            found.append(
                {
                    "payee": payee,
                    "amount": milliunit_to_amount(round(median)),
                    "day": int(statistics.median(int(tx["date"][8:10]) for tx in txs)),
                    "months_seen": len(per_month),
                }
            )
    return found


def _other_average(
    transactions: list[dict[str, Any]], today: date, known: list[Recurring], outflow: bool
) -> float:
    """Monthly average over the last 3 full months of one direction, recurring excluded."""
    months = set(_months_before(today, VARIABLE_MONTHS))
    recurring_payees = {r["payee"] for r in known if (r["amount"] < 0) == outflow}
    total = sum(
        tx["amount"]
        for tx in transactions
        if _usable(tx)
        and (tx["amount"] < 0) == outflow
        and tx["date"][:7] in months
        and normalize_payee(tx.get("payee_name") or "") not in recurring_payees
    )
    return milliunit_to_amount(round(total / VARIABLE_MONTHS))


def variable_average(
    transactions: list[dict[str, Any]], today: date, known: list[Recurring]
) -> float:
    """Average monthly outflow over the last 3 full months, recurring charges excluded."""
    return _other_average(transactions, today, known, outflow=True)


def income_average(
    transactions: list[dict[str, Any]], today: date, known: list[Recurring]
) -> float:
    """Average monthly inflow over the last 3 full months, recurring income excluded."""
    return _other_average(transactions, today, known, outflow=False)


def month_to_date(
    transactions: list[dict[str, Any]], today: date, known: list[Recurring]
) -> tuple[float, float]:
    """(spent, received) since the 1st of this month, recurring amounts excluded."""
    this_month = today.isoformat()[:7]
    recurring_payees = {(r["payee"], r["amount"] < 0) for r in known}
    spent = received = 0
    for tx in transactions:
        if not _usable(tx) or tx["date"][:7] != this_month:
            continue
        payee = normalize_payee(tx.get("payee_name") or "")
        if (payee, tx["amount"] < 0) in recurring_payees:
            continue
        if tx["amount"] < 0:
            spent += tx["amount"]
        else:
            received += tx["amount"]
    return milliunit_to_amount(spent), milliunit_to_amount(received)


def _horizon(today: date, until: str) -> list[tuple[int, int]]:
    year, month = today.year, today.month
    end_year, end_month = (int(part) for part in until.split("-"))
    months = []
    while (year, month) <= (end_year, end_month):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def _spread(total: int, first_day: int, last_day: int) -> dict[int, int]:
    """Split `total` milliunits evenly over the days, in whole cents, summing exactly."""
    days = last_day - first_day + 1
    if days <= 0 or not total:
        return {}
    cents = total // 10
    base, extra = divmod(cents, days)
    return {first_day + i: (base + (1 if i < extra else 0)) * 10 for i in range(days)}


def project(  # pylint: disable=too-many-arguments,too-many-locals
    *,
    start_balance: float,
    today: date,
    until: str,
    recurring: list[Recurring],  # pylint: disable=redefined-outer-name
    variable_monthly: float,
    monthly_income: float,
    one_offs: list[OneOff],
    spent_this_month: float = 0.0,
    received_this_month: float = 0.0,
) -> Projection:
    """Walk day by day from tomorrow to the end of `until` ("YYYY-MM").

    Variable spending and income are spread evenly over the days; recurring
    amounts and one-offs fall on their dates. For the current month, only what
    is left is projected: the averages minus what was already spent
    (`spent_this_month`, negative) and received (`received_this_month`), and
    recurring amounts dated after today.
    """
    balance = amount_to_milliunit(start_balance)
    variable = amount_to_milliunit(variable_monthly)
    income = amount_to_milliunit(monthly_income)
    months: list[MonthProjection] = []
    first_shortfall = None
    for year, month in _horizon(today, until):
        days = calendar.monthrange(year, month)[1]
        current = (year, month) == (today.year, today.month)
        label = f"{year:04d}-{month:02d}"
        first_day = today.day + 1 if current else 1
        to_spend = min(0, variable - amount_to_milliunit(spent_this_month)) if current else variable
        to_receive = (
            max(0, income - amount_to_milliunit(received_this_month)) if current else income
        )
        dated: dict[int, int] = defaultdict(int)
        for r in recurring:
            if r["day"] >= first_day:
                dated[min(r["day"], days)] += amount_to_milliunit(r["amount"])
        for o in one_offs:
            if o["date"][:7] == label and o["date"] > today.isoformat():
                dated[int(o["date"][8:10])] += amount_to_milliunit(o["amount"])
        spending = _spread(to_spend, first_day, days)
        receiving = _spread(to_receive, first_day, days)
        start = running = lowest = balance
        for day in range(first_day, days + 1):
            running += spending.get(day, 0) + receiving.get(day, 0) + dated.get(day, 0)
            lowest = min(lowest, running)
        flows = list(dated.values()) + [sum(spending.values()), sum(receiving.values())]
        months.append(
            {
                "month": label,
                "start": milliunit_to_amount(start),
                "inflows": milliunit_to_amount(sum(a for a in flows if a > 0)),
                "outflows": milliunit_to_amount(sum(a for a in flows if a < 0)),
                "end": milliunit_to_amount(running),
                "lowest": milliunit_to_amount(lowest),
            }
        )
        if lowest < 0 and first_shortfall is None:
            first_shortfall = label
        balance = running
    return {"months": months, "first_shortfall": first_shortfall}
