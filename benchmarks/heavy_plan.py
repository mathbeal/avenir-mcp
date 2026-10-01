# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""A heavy invented plan: five years of a busy household, in YNAB's shapes.

About 150 transactions a month for 60 months (some 9,000), 60 merchants whose bank
labels change every time (card numbers, dates, SEPA prefixes), 30 categories, two
accounts, and 20 scheduled transactions. Seeded: every run measures the same data.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

TODAY = date(2026, 9, 25)
MONTHS = 60
PER_MONTH = 150
GROUPS = {
    "Bills": ["Rent", "Electricity", "Phone", "Internet", "Insurance", "Water"],
    "Everyday": ["Groceries", "Restaurants", "Transport", "Fuel", "Pharmacy", "Household"],
    "Fun": ["Tennis", "Cinema", "Books", "Subscriptions", "Games", "Travel"],
    "Family": ["School", "Clothes", "Gifts", "Childcare", "Pets", "Health"],
    "Savings goals": ["Holidays", "Car", "Emergency", "Home", "Projects", "Taxes"],
}
PREFIXES = ["CB ", "CARTE ", "PRLV SEPA ", "VIR ", ""]


def categories() -> list[dict[str, Any]]:
    """The plan's categories, as YNAB lists them."""
    return [
        {"id": f"cat-{name.lower()}", "name": name}
        | {"category_group_id": f"grp-{group.lower().replace(' ', '-')}"}
        | {"category_group_name": group, "hidden": False, "deleted": False}
        for group, names in GROUPS.items()
        for name in names
    ]


def accounts() -> list[dict[str, Any]]:
    """Two on-budget accounts."""
    return [
        {"id": "acc-checking", "name": "Checking", "on_budget": True, "closed": False},
        {"id": "acc-savings", "name": "Savings", "on_budget": True, "closed": False},
    ]


def _merchants(rng: random.Random) -> list[tuple[str, str, int]]:
    """Sixty merchants: a name, the category they are usually filed in, a typical amount."""
    cats = [c["id"] for c in categories()]
    return [(f"MERCHANT {i:02d}", rng.choice(cats), rng.randint(3_000, 180_000)) for i in range(60)]


def _label(rng: random.Random, merchant: str, day: date) -> str:
    """A bank label for one payment: prefix, name, date and masked card as banks write them."""
    card = f"{rng.randint(400000, 599999)}******{rng.randint(0, 9)}"
    return f"{rng.choice(PREFIXES)}{merchant} FACT {day:%d%m%y} {card}"


def transactions(seed: int = 7) -> list[dict[str, Any]]:
    """Five years of transactions, newest last; 5 % pending (no category)."""
    rng = random.Random(seed)
    merchants = _merchants(rng)
    start = TODAY.replace(day=1) - timedelta(days=30 * MONTHS)
    out = []
    for n in range(MONTHS * PER_MONTH):
        name, category, typical = rng.choice(merchants)
        day = start + timedelta(days=n * 30 * MONTHS // (MONTHS * PER_MONTH))
        pending = rng.random() < 0.05
        out.append(
            {
                "id": f"tx-{n:05d}",
                "date": day.isoformat(),
                "amount": -round(typical * rng.uniform(0.8, 1.2)),
                "memo": None,
                "cleared": "cleared" if rng.random() < 0.9 else "uncleared",
                "approved": not pending,
                "account_id": "acc-checking",
                "account_name": "Checking",
                "payee_name": _label(rng, name, day),
                "category_id": None if pending else category,
                "category_name": None,
                "transfer_account_id": None,
                "deleted": False,
                "subtransactions": [],
            }
        )
    return out


def scheduled() -> list[dict[str, Any]]:
    """Twenty scheduled transactions, monthly and yearly."""
    rng = random.Random(11)
    return [
        {
            "id": f"sch-{n:02d}",
            "date_first": "2025-01-05",
            "date_next": (TODAY + timedelta(days=rng.randint(1, 28))).isoformat(),
            "frequency": "monthly" if n % 4 else "yearly",
            "amount": -rng.randint(10_000, 900_000),
            "memo": None,
            "account_id": "acc-checking",
            "payee_name": f"MERCHANT {n:02d}",
            "category_id": categories()[n]["id"],
            "transfer_account_id": None,
            "deleted": False,
            "subtransactions": [],
        }
        for n in range(20)
    ]


def month_categories(month: str, txs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One month's categories with budgeted, activity and balance, from the transactions."""
    spent: dict[str, int] = {}
    for tx in txs:
        if tx["date"][:7] == month[:7] and tx["category_id"]:
            spent[tx["category_id"]] = spent.get(tx["category_id"], 0) + tx["amount"]
    return [
        {
            **cat,
            "budgeted": 200_000,
            "activity": spent.get(cat["id"], 0),
            "balance": 200_000 + spent.get(cat["id"], 0),
        }
        for cat in categories()
    ]
