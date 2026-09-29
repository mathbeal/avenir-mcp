"""Tests for journal.py — the local record that makes writes undoable."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from avenir_mcp import journal

_MOVES = [
    journal.Move(transaction_id="t1", from_category_id=None, to_category_id="c-food"),
    journal.Move(transaction_id="t2", from_category_id="c-fun", to_category_id="c-food"),
]


def _found(book: journal.Journal, plan_id: str, operation_id: str | None = None) -> journal.Entry:
    entry = book.find(plan_id, operation_id)
    assert entry is not None
    return entry


def test_recorded_operation_can_be_found_again(tmp_path: Path) -> None:
    """An operation is found by id, with its moves."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    op_id = book.record("b1", "categorize", _MOVES)
    entry = book.find("b1", op_id)
    assert entry is not None
    assert entry.operation_id == op_id
    assert entry.kind == "categorize"
    assert entry.moves == _MOVES


def test_latest_returns_the_last_operation_not_yet_undone(tmp_path: Path) -> None:
    """Undo without an id targets the most recent operation still in effect."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    first = book.record("b1", "categorize", _MOVES)
    second = book.record("b1", "categorize", _MOVES)
    book.record("b2", "categorize", _MOVES)
    assert _found(book, "b1").operation_id == second
    book.mark_undone(second)
    assert _found(book, "b1").operation_id == first
    book.mark_undone(first)
    assert book.find("b1") is None


def test_undone_or_foreign_operation_is_not_found(tmp_path: Path) -> None:
    """An undone operation, or one from another budget, cannot be undone again."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    op_id = book.record("b1", "categorize", _MOVES)
    assert book.find("b2", op_id) is None
    book.mark_undone(op_id)
    assert book.find("b1", op_id) is None


def test_journal_survives_a_restart(tmp_path: Path) -> None:
    """The record is on disk: a new server process sees earlier operations."""
    path = tmp_path / "journal.jsonl"
    op_id = journal.Journal(path).record("b1", "categorize", _MOVES)
    assert journal.Journal(path).find("b1", op_id) is not None


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions; Windows uses ACLs")
def test_journal_file_is_private_and_holds_no_amounts_or_names(tmp_path: Path) -> None:
    """Only the owner can read it, and it stores identifiers only."""
    path = tmp_path / "sub" / "journal.jsonl"
    journal.Journal(path).record("b1", "categorize", _MOVES)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    text = path.read_text(encoding="utf-8")
    assert "amount" not in text and "payee" not in text


def test_a_budget_change_keeps_its_amounts_and_nothing_about_transactions(tmp_path: Path) -> None:
    """A budget line holds the amounts assigned before and after, which undo restores; no payee."""
    path = tmp_path / "journal.jsonl"
    journal.Journal(path).record(
        "b1",
        "budget",
        [],
        {"month": "2026-09-01", "category_id": "c1", "from": 120000, "to": 150000},
    )
    text = path.read_text(encoding="utf-8")
    assert '"from":120000' in text and '"to":150000' in text
    assert "payee" not in text and "memo" not in text


def test_missing_journal_is_empty(tmp_path: Path) -> None:
    """Before the first write there is nothing to undo."""
    assert journal.Journal(tmp_path / "none.jsonl").find("b1") is None


def test_default_path_follows_xdg_state_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without AVENIR_MCP_JOURNAL, the journal lives under the XDG state directory."""
    monkeypatch.delenv("AVENIR_MCP_JOURNAL", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert journal.default_path() == tmp_path / "avenir-mcp" / "journal.jsonl"


def test_default_path_falls_back_to_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without XDG_STATE_HOME, it lives in ~/.local/state."""
    monkeypatch.delenv("AVENIR_MCP_JOURNAL", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert journal.default_path() == tmp_path / ".local" / "state" / "avenir-mcp" / "journal.jsonl"


def test_env_variable_overrides_the_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_JOURNAL chooses the file."""
    monkeypatch.setenv("AVENIR_MCP_JOURNAL", str(tmp_path / "mine.jsonl"))
    assert journal.default_path() == tmp_path / "mine.jsonl"


def test_older_operation_can_be_named_while_newer_ones_exist(tmp_path: Path) -> None:
    """Undo by id reaches past more recent operations."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    first = book.record("b1", "categorize", _MOVES)
    book.record("b1", "categorize", _MOVES)
    assert _found(book, "b1", first).operation_id == first


def test_operation_details_are_kept(tmp_path: Path) -> None:
    """Operations other than recategorisation keep what undo needs, as identifiers."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    details = {"account_id": "acc", "reconciled_ids": ["t1"], "adjustment_id": "t9"}
    op_id = book.record("b1", "reconcile", [], details)
    assert _found(book, "b1", op_id).details == details
    other = book.record("b1", "categorize", _MOVES)
    assert _found(book, "b1", other).details == {}


def test_a_line_written_by_an_earlier_version_is_still_read(tmp_path: Path) -> None:
    """An operation recorded without details, or with a field unknown here, stays undoable."""
    path = tmp_path / "journal.jsonl"
    path.write_text(
        '{"operation_id":"op1","plan_id":"b1","kind":"categorize",'
        '"applied_at":"2026-09-01T10:00:00+00:00","moves":[],"origin":"cli"}\n',
        encoding="utf-8",
    )
    entry = journal.Journal(path).find("b1")
    assert entry is not None
    assert (entry.operation_id, entry.details) == ("op1", {})


@pytest.mark.parametrize(
    "line", ["not json", '{"operation_id": "op1"}', '["undone"]', '{"undone": 3}']
)
def test_a_damaged_line_is_named_with_a_way_forward(tmp_path: Path, line: str) -> None:
    """A line that is not an operation stops the reading and says which one it is."""
    path = tmp_path / "journal.jsonl"
    journal.Journal(path).record("b1", "categorize", _MOVES)
    with path.open("a", encoding="utf-8") as file:
        file.write("\n" + line + "\n")
    with pytest.raises(ValueError, match=r"line 3, is not a journal entry"):
        journal.Journal(path).find("b1")


def test_an_operation_recorded_with_budget_id_is_still_found(tmp_path: Path) -> None:
    """Journals written before YNAB's plans named the budget: those lines stay undoable."""
    path = tmp_path / "journal.jsonl"
    path.write_text(
        '{"operation_id":"op1","budget_id":"b1","kind":"categorize",'
        '"applied_at":"2026-09-01T10:00:00+00:00","moves":[]}\n',
        encoding="utf-8",
    )
    entry = journal.Journal(path).find("b1")
    assert entry is not None
    assert (entry.operation_id, entry.plan_id) == ("op1", "b1")
