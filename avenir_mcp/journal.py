"""A local, append-only record of the writes made through the server.

Each applied operation is one JSON line holding identifiers only: which
transaction moved from which category to which. Undoing an operation appends
a line that marks it undone. Amounts, payees and memos are never stored.
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict


class Move(TypedDict):
    """One transaction's category before and after an operation."""

    transaction_id: str
    from_category_id: str | None
    to_category_id: str | None


class Entry(TypedDict):
    """An operation as recorded in the journal."""

    operation_id: str
    budget_id: str
    kind: str
    applied_at: str
    moves: list[Move]
    details: dict[str, Any]


def default_path() -> Path:
    """Return AVENIR_MCP_JOURNAL, or journal.jsonl in the XDG state directory."""
    configured = os.getenv("AVENIR_MCP_JOURNAL")
    if configured:
        return Path(configured)
    state_home = os.getenv("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "avenir-mcp" / "journal.jsonl"


class Journal:
    """Operations applied through the server, newest last."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _append(self, line: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as file:
            file.write(json.dumps(line, separators=(",", ":")) + "\n")

    def _lines(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def record(
        self,
        budget_id: str,
        kind: str,
        moves: list[Move],
        details: dict[str, Any] | None = None,
    ) -> str:
        """Append an applied operation and return its id.

        `details` holds what undoing an operation other than a recategorisation
        needs, as identifiers only.
        """
        operation_id = secrets.token_hex(6)
        entry: Entry = {
            "operation_id": operation_id,
            "budget_id": budget_id,
            "kind": kind,
            "applied_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "moves": moves,
            "details": details or {},
        }
        self._append(dict(entry))
        return operation_id

    def mark_undone(self, operation_id: str) -> None:
        """Record that an operation has been undone."""
        self._append({"undone": operation_id})

    def find(self, budget_id: str, operation_id: str | None = None) -> Entry | None:
        """Return an operation of this budget still in effect.

        With no id, return the most recent one; None if there is none.
        """
        lines = self._lines()
        undone = {line["undone"] for line in lines if "undone" in line}
        for line in reversed(lines):
            if "undone" in line or line["operation_id"] in undone:
                continue
            if line["budget_id"] != budget_id:
                continue
            if operation_id is None or line["operation_id"] == operation_id:
                return {
                    "operation_id": line["operation_id"],
                    "budget_id": line["budget_id"],
                    "kind": line["kind"],
                    "applied_at": line["applied_at"],
                    "moves": line["moves"],
                    "details": line.get("details", {}),
                }
        return None
