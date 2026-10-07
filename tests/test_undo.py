# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for tools_undo.py — the steps every undo shares, apart from the tools."""

from __future__ import annotations

from pathlib import Path

from avenir_mcp import journal, tools_undo


def _entry(book: journal.Journal) -> journal.Entry:
    book.record("b1", "target", [], {"category_id": "c-food"})
    entry = book.find("b1")
    assert entry is not None
    return entry


def test_an_undone_operation_leaves_the_journal_with_nothing_to_undo(tmp_path: Path) -> None:
    """Recording the undo takes the operation out of what undo_operation would find."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    entry = _entry(book)
    result = tools_undo._undone(book, entry, "Target restored.")  # pylint: disable=protected-access
    assert result.status == "applied"
    assert result.message == "Target restored."
    assert result.conflicts == []
    assert book.find("b1") is None


def test_what_an_undo_left_alone_is_reported_as_a_conflict(tmp_path: Path) -> None:
    """Ids the undo could not put back are returned, not dropped."""
    book = journal.Journal(tmp_path / "journal.jsonl")
    # pylint: disable-next=protected-access
    result = tools_undo._undone(book, _entry(book), "Flags restored.", ["t1", "t2"])
    assert result.conflicts == ["t1", "t2"]
