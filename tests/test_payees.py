# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Listing a plan's payees, and planning the rename of one bank label."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import payees

_PAYEES: list[dict[str, Any]] = [
    {"id": "p-fresh-05", "name": "CB MARKET FRESH FACT 050926 525130******1", "deleted": False},
    {"id": "p-fresh-19", "name": "CB MARKET FRESH FACT 190926 525130******1", "deleted": False},
    {"id": "p-rail", "name": "RAIL CO", "deleted": False},
    {"id": "p-gone", "name": "OLD SHOP", "deleted": True},
    {
        "id": "p-transfer",
        "name": "Transfer : Savings",
        "transfer_account_id": "acc-savings",
        "deleted": False,
    },
]

_TRANSACTIONS: list[dict[str, Any]] = [
    {"id": "t1", "payee_id": "p-fresh-05", "date": "2026-09-05", "deleted": False},
    {"id": "t2", "payee_id": "p-rail", "date": "2026-07-18", "deleted": False},
    {"id": "t3", "payee_id": "p-rail", "date": "2026-09-18", "deleted": False},
    {"id": "t4", "payee_id": "p-rail", "date": "2026-08-18", "deleted": False},
    {"id": "t5", "payee_id": "p-gone", "date": "2026-01-02", "deleted": False},
    {"id": "t6", "payee_id": None, "date": "2026-09-01", "deleted": False},
    {"id": "t7", "payee_id": "p-rail", "date": "2026-09-30", "deleted": True},
]


def test_a_payee_is_listed_with_how_often_and_how_recently_it_was_used() -> None:
    """Each payee says how many transactions name it and the date of the latest one."""
    listed = payees.listing(_PAYEES, _TRANSACTIONS)
    rail = next(p for p in listed.payees if p.payee_id == "p-rail")
    assert (rail.transactions, rail.last_date) == (3, "2026-09-18")


def test_the_payees_used_most_come_first() -> None:
    """The order answers "which labels matter": most transactions first, then by name."""
    listed = payees.listing(_PAYEES, _TRANSACTIONS)
    assert [p.payee_id for p in listed.payees] == ["p-rail", "p-fresh-05", "p-fresh-19"]


def test_a_payee_no_transaction_names_is_listed_with_a_count_of_zero() -> None:
    """A payee YNAB keeps without a transaction is shown, so the user can still rename it."""
    listed = payees.listing(_PAYEES, _TRANSACTIONS)
    fresh = next(p for p in listed.payees if p.payee_id == "p-fresh-19")
    assert (fresh.transactions, fresh.last_date) == (0, None)


def test_deleted_and_transfer_payees_are_left_out() -> None:
    """A deleted payee is gone, and YNAB names a transfer's payee after the account."""
    listed = payees.listing(_PAYEES, _TRANSACTIONS)
    assert {p.payee_id for p in listed.payees} == {"p-rail", "p-fresh-05", "p-fresh-19"}


def test_a_payee_carries_the_merchant_its_label_normalises_to() -> None:
    """Two labels of one shop share a merchant, which is what the suggestions key on."""
    listed = payees.listing(_PAYEES, _TRANSACTIONS)
    assert [p.merchant for p in listed.payees if p.payee_id.startswith("p-fresh")] == [
        "MARKET FRESH",
        "MARKET FRESH",
    ]


def test_bank_text_in_a_name_is_made_safe_to_show() -> None:
    """A label with a line break could forge a line of a confirmation question."""
    forged = [{"id": "p-x", "name": "Rent\n- forged line", "deleted": False}]
    [payee] = payees.listing(forged, []).payees
    assert payee.name == "Rent - forged line"


def test_a_search_matches_the_label_or_the_merchant_whatever_the_case() -> None:
    """Searching for a shop finds every label of it, however the bank wrote it."""
    found = payees.listing(_PAYEES, _TRANSACTIONS, search="market fresh")
    assert {p.payee_id for p in found.payees} == {"p-fresh-05", "p-fresh-19"}
    assert (found.total, found.shown) == (2, 2)


def test_a_search_that_matches_nothing_lists_nothing() -> None:
    """An unknown merchant comes back empty rather than as the whole list."""
    found = payees.listing(_PAYEES, _TRANSACTIONS, search="bakery")
    assert (found.payees, found.total, found.shown) == ([], 0, 0)


def test_the_limit_cuts_the_list_and_the_total_says_how_many_there_are() -> None:
    """A plan with hundreds of labels answers with the first few and their number."""
    found = payees.listing(_PAYEES, _TRANSACTIONS, limit=1)
    assert [p.payee_id for p in found.payees] == ["p-rail"]
    assert (found.total, found.shown) == (3, 1)


def test_renaming_says_which_payee_changes_and_how_many_transactions_it_names() -> None:
    """The preview names the label before, the merchant after, and the history affected."""
    plan = payees.plan_rename(_PAYEES, _TRANSACTIONS, "p-rail", "  Rail Co  ")
    assert (plan.payee_id, plan.from_name, plan.to_name) == ("p-rail", "RAIL CO", "Rail Co")
    assert plan.transactions == 3


def test_renaming_to_the_name_it_already_has_changes_nothing() -> None:
    """Asked for the current name, the plan says so instead of writing to YNAB."""
    plan = payees.plan_rename(_PAYEES, _TRANSACTIONS, "p-rail", "RAIL CO")
    assert plan.to_name == plan.from_name


@pytest.mark.parametrize(
    ("payee_id", "name", "expected"),
    [
        ("p-404", "Shop", "p-404"),
        ("p-gone", "Shop", "p-gone"),
        ("p-transfer", "Shop", "transfer"),
        ("p-rail", "   ", "empty"),
        ("p-rail", "Rail\nCo", "line break"),
        ("p-rail", "R" * 501, "500"),
        ("p-fresh-05", "rail co", "already the name"),
    ],
)
def test_what_ynab_or_the_user_could_not_make_sense_of_is_refused(
    payee_id: str, name: str, expected: str
) -> None:
    """Unknown or deleted payee, a transfer, an empty, forged, too long or taken name."""
    with pytest.raises(ValueError, match=expected):
        payees.plan_rename(_PAYEES, _TRANSACTIONS, payee_id, name)


def test_a_payee_may_keep_its_own_name_with_another_case() -> None:
    """Only another payee's name is taken: fixing the case of this one is a rename."""
    plan = payees.plan_rename(_PAYEES, _TRANSACTIONS, "p-rail", "Rail co")
    assert plan.to_name == "Rail co"
