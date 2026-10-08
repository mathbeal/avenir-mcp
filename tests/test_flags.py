# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for flags.py — what each transaction's flag is, and what it would become."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import flags


def _tx(tx_id: str, color: str | None = None, **extra: Any) -> dict[str, Any]:
    tx: dict[str, Any] = {
        "id": tx_id,
        "date": "2026-09-10",
        "payee_name": "Corner Shop",
        "amount": -4_500,
        "flag_color": color,
        "deleted": False,
    }
    tx.update(extra)
    return tx


@pytest.mark.parametrize(
    "stored",
    [None, "", "pink", "Red"],
    ids=["null", "empty", "outside YNAB's list", "wrong case"],
)
def test_a_flag_colour_ynab_does_not_list_reads_as_no_flag(stored: str | None) -> None:
    """Null, empty or a value of an old transaction: all mean the transaction has no flag."""
    assert flags.current(_tx("t1", stored)) is None


def test_a_colour_ynab_lists_is_read_as_it_is() -> None:
    """The six colours YNAB offers come back unchanged."""
    assert [flags.current(_tx("t1", color)) for color in flags.COLORS] == list(flags.COLORS)


def test_asking_for_no_flag_at_all_is_refused() -> None:
    """An empty list is a mistake worth naming, not an empty plan."""
    with pytest.raises(ValueError) as refusal:
        flags.plan_flags([_tx("t1")], [])
    assert str(refusal.value) == "Give at least one flag."


def test_a_transaction_named_twice_is_refused_and_listed() -> None:
    """Two flags for one transaction: which one wins is not for avenir-mcp to guess."""
    asked = [
        flags.Flag(transaction_id="t1", color="red"),
        flags.Flag(transaction_id="t2", color="blue"),
        flags.Flag(transaction_id="t2", color="green"),
        flags.Flag(transaction_id="t1", color="purple"),
    ]
    with pytest.raises(ValueError) as refusal:
        flags.plan_flags([_tx("t1"), _tx("t2")], asked)
    assert str(refusal.value) == "Transaction t1, t2 is named twice: give one flag each."


def test_transactions_not_in_the_plan_are_refused_and_listed_with_where_to_find_one() -> None:
    """Every unknown id is named, in the order asked, with the tool that gives real ones."""
    asked = [
        flags.Flag(transaction_id="t9", color="red"),
        flags.Flag(transaction_id="t1", color="red"),
        flags.Flag(transaction_id="t8", color="red"),
    ]
    with pytest.raises(ValueError) as refusal:
        flags.plan_flags([_tx("t1")], asked)
    assert str(refusal.value) == (
        "Transaction t9, t8 is not in this plan: use a transaction_id from find_transactions."
    )


def test_a_deleted_transaction_is_not_in_the_plan() -> None:
    """YNAB still returns it; flagging it would change nothing a user can see."""
    with pytest.raises(ValueError, match="not in this plan"):
        flags.plan_flags(
            [_tx("gone", deleted=True), _tx("t1")],
            [flags.Flag(transaction_id="gone", color="red")],
        )


def test_a_flag_the_transaction_already_has_is_counted_not_changed() -> None:
    """Asking for the colour already there is not an error, and not a write either."""
    asked = [
        flags.Flag(transaction_id="t1", color="red"),
        flags.Flag(transaction_id="t2", color="blue"),
    ]
    plan = flags.plan_flags([_tx("t1", "red"), _tx("t2", "green")], asked)
    assert [(change.transaction_id, change.to_color) for change in plan.changes] == [("t2", "blue")]
    assert plan.unchanged_count == 1


def test_removing_a_flag_is_a_change_and_keeps_the_colour_it_had() -> None:
    """A change says both colours, and shows the payee on one line."""
    [change] = flags.plan_flags(
        [_tx("t1", "orange", payee_name="CB CAFE\u202e")],
        [flags.Flag(transaction_id="t1")],
    ).changes
    assert (change.from_color, change.to_color) == ("orange", None)
    assert (change.date, change.payee, change.amount) == ("2026-09-10", "CB CAFE", -4.5)
