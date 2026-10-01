"""set_category_budget through the MCP protocol: preview, confirm, journal, undo."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from .fake_month import FakeMonth, serving
from .mcp_helpers import FLAT, FORGED, accept, asking, call, decline, one_line


@pytest.fixture(name="month")
def _month(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeMonth]:
    fake = FakeMonth({"c-food": "Restaurants", "c-fun": "Leisure"}, {"c-food": 200000, "c-fun": 0})
    with serving(fake, tmp_path, monkeypatch):
        yield fake


_ARGS = {"plan_id": "b1", "month": "2026-10-01", "category_id": "c-food", "amount": 150.0}


def test_budget_change_is_previewed_in_currency_then_applied_with_the_code(
    month: FakeMonth,
) -> None:
    """The preview names the category and both amounts; the code applies it."""
    preview = call("set_category_budget", _ARGS).structured_content
    assert preview["status"] == "confirmation_required"
    assert (preview["category"], preview["from_amount"], preview["to_amount"]) == (
        "Restaurants",
        200.0,
        150.0,
    )
    assert not month.sets
    done = call("set_category_budget", {**_ARGS, "confirmation": preview["confirmation"]})
    assert done.structured_content["status"] == "applied"
    assert month.sets == [("2026-10-01", "c-food", 150.0)]


def test_budget_change_is_undone_to_the_previous_amount(month: FakeMonth) -> None:
    """undo_operation puts the category back to what it had."""
    call("set_category_budget", _ARGS, accept)
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "applied"
    assert month.sets[-1] == ("2026-10-01", "c-food", 200.0)


def test_undo_leaves_a_budget_changed_since_alone(month: FakeMonth) -> None:
    """If the amount moved again after the operation, undo does not overwrite it."""
    call("set_category_budget", _ARGS, accept)
    month.budgeted["c-food"] = 999000
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "nothing_to_do"
    assert undo["conflicts"] == ["c-food"]
    assert len(month.sets) == 1


def test_same_amount_changes_nothing(month: FakeMonth) -> None:
    """Setting the current amount again asks and writes nothing."""
    data = call("set_category_budget", {**_ARGS, "amount": 200.0}).structured_content
    assert data["status"] == "nothing_to_do"
    assert not month.sets


def test_declined_budget_change_writes_nothing(month: FakeMonth) -> None:
    """If the user says no, the amount stays."""
    assert call("set_category_budget", _ARGS, decline).structured_content["status"] == "declined"
    assert not month.sets


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"category_id": "c-404"}, "c-404"),
        ({"month": "2026-10"}, "YYYY-MM-01"),
    ],
)
def test_invalid_budget_change_is_a_tool_error(
    month: FakeMonth, args: dict[str, Any], expected: str
) -> None:
    """Unknown category or malformed month is refused before anything is asked."""
    result = call("set_category_budget", {**_ARGS, **args})
    assert result.is_error
    assert expected in result.content[0].text
    assert not month.sets


def test_declined_undo_keeps_the_new_amount(month: FakeMonth) -> None:
    """If the user refuses the undo, the budget keeps its new amount."""
    call("set_category_budget", _ARGS, accept)
    undo = call("undo_operation", {"plan_id": "b1"}, decline).structured_content
    assert undo["status"] == "declined"
    assert month.sets == [("2026-10-01", "c-food", 150.0)]


def test_a_category_name_cannot_forge_lines_in_the_question(month: FakeMonth) -> None:
    """A category name with a line break stays on one line, in the question and the preview."""
    month.names["c-food"] = FORGED
    asked: list[str] = []
    data = call("set_category_budget", _ARGS, asking(asked)).structured_content
    assert one_line(asked[0])
    assert data["category"] == FLAT


def test_a_category_name_cannot_forge_lines_in_the_undo_question(month: FakeMonth) -> None:
    """Undoing a budget change names the category on one line."""
    call("set_category_budget", _ARGS, accept)
    month.names["c-food"] = FORGED
    asked: list[str] = []
    call("undo_operation", {"plan_id": "b1"}, asking(asked))
    assert one_line(asked[0])
