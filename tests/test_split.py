"""Tests for split.py — planning how a transaction is split across categories."""

from __future__ import annotations

from typing import Any

import pytest

from avenir_mcp import split
from avenir_mcp.split import SplitLine

_CATEGORIES: list[dict[str, Any]] = [
    {"id": "c-food", "name": "Groceries"},
    {"id": "c-home", "name": "Household"},
    {"id": "c-none", "name": "Uncategorized", "category_group_name": "Internal Master Category"},
]


def _tx(**extra: Any) -> dict[str, Any]:
    tx: dict[str, Any] = {
        "id": "t1",
        "account_id": "acc",
        "date": "2026-09-12",
        "amount": -86400,
        "payee_name": "Organic Market",
        "category_id": None,
        "transfer_account_id": None,
        "subtransactions": [],
    }
    tx.update(extra)
    return tx


def _lines(*pairs: tuple[float, str]) -> list[SplitLine]:
    return [SplitLine(amount=amount, category_id=cat) for amount, cat in pairs]


_GOOD = _lines((-81.15, "c-food"), (-5.25, "c-home"))


def _plan(tx: dict[str, Any] | None = None, lines: list[SplitLine] = _GOOD, **kw: Any) -> Any:
    return split.plan_split([tx or _tx()], _CATEGORIES, "t1", lines, **kw)


def test_plan_names_each_line_category_and_the_transaction() -> None:
    """The preview shows the transaction and, per line, its amount and category name."""
    plan = _plan(lines=[*_GOOD[:1], SplitLine(amount=-5.25, category_id="c-home", memo="Soap")])
    assert plan.transaction_id == "t1"
    assert plan.date == "2026-09-12"
    assert plan.payee == "Organic Market"
    assert plan.amount == -86.40
    assert plan.from_category is None
    assert [(line.amount, line.category, line.memo) for line in plan.lines] == [
        (-81.15, "Groceries", None),
        (-5.25, "Household", "Soap"),
    ]


def test_plan_names_the_category_the_split_replaces() -> None:
    """A categorised transaction can be split; the preview says which category it leaves."""
    assert _plan(_tx(category_id="c-food")).from_category == "Groceries"


def test_plan_makes_untrusted_text_safe_to_show() -> None:
    """Payee and memo reach the question on one visible line."""
    lines = [*_GOOD[:1], SplitLine(amount=-5.25, category_id="c-home", memo="a\nb")]
    plan = _plan(_tx(payee_name="Shop" + chr(0x202E) + "\nForged"), lines)
    assert plan.payee == "Shop Forged"
    assert plan.lines[1].memo == "a b"


def test_lines_must_add_up_to_the_transaction_to_the_cent() -> None:
    """A difference of one cent is refused, and the message gives both totals."""
    with pytest.raises(ValueError, match=r"-86\.39.*-86\.40"):
        _plan(lines=_lines((-81.15, "c-food"), (-5.24, "c-home")))


def test_float_drift_does_not_break_an_exact_sum() -> None:
    """Amounts are compared in milliunits: 0.1 + 0.2 style drift is not a difference."""
    tx = _tx(amount=-300)
    assert _plan(tx, _lines((-0.1, "c-food"), (-0.2, "c-home"))).amount == -0.3


def test_a_line_may_go_the_other_way() -> None:
    """A deposit refunded on the receipt is a positive line; only the total must match."""
    plan = _plan(lines=_lines((-86.90, "c-food"), (0.5, "c-home")))
    assert [line.amount for line in plan.lines] == [-86.90, 0.5]


@pytest.mark.parametrize(
    ("tx", "lines", "message"),
    [
        (None, _lines((-86.40, "c-food")), "at least two lines"),
        (None, _lines((-86.40, "c-food"), (0, "c-home")), "zero"),
        (None, _lines((-81.15, "c-food"), (-5.25, "c-gone")), "not in this budget"),
        (None, _lines((-81.15, "c-food"), (-5.25, "c-none")), "Uncategorized"),
        (_tx(subtransactions=[{"id": "s1"}]), _GOOD, "already split"),
        (_tx(transfer_account_id="acc2"), _GOOD, "transfer"),
        (_tx(account_id="tracking"), _GOOD, "off-budget"),
        (_tx(deleted=True), _GOOD, "deleted"),
    ],
)
def test_what_cannot_be_split_is_refused_with_what_to_do(
    tx: dict[str, Any] | None, lines: list[SplitLine], message: str
) -> None:
    """Each refusal says what is wrong, so the agent can fix its call."""
    with pytest.raises(ValueError, match=message):
        _plan(tx, lines, off_budget={"tracking"})


def test_an_unknown_transaction_is_refused() -> None:
    """The id must come from the budget."""
    with pytest.raises(ValueError, match="suggest_categories"):
        split.plan_split([_tx()], _CATEGORIES, "t-gone", _GOOD)


def test_a_deleted_subtransaction_list_does_not_count_as_a_split() -> None:
    """Only live lines make a split: YNAB can keep deleted ones in a delta."""
    assert _plan(_tx(subtransactions=[{"id": "s1", "deleted": True}])).transaction_id == "t1"


def test_memo_longer_than_ynab_allows_is_refused_by_the_schema() -> None:
    """YNAB keeps 500 characters of memo: longer is refused before any call."""
    with pytest.raises(ValueError, match="500"):
        SplitLine(amount=-1, category_id="c-food", memo="x" * 501)
