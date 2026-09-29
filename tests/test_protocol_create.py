"""create_transactions through the MCP protocol: validate, preview, confirm, undo."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from .mcp_helpers import accept, call, decline

_ACCOUNTS = [{"id": "acc", "name": "Checking"}]
_CATS = [{"id": "c-food", "name": "Groceries"}]
_ITEM = {
    "date": "2026-09-20",
    "amount": -12.5,
    "payee_name": "Corner Shop",
    "category_id": "c-food",
}


class _Ledger:
    """A fake account that records creations and deletions."""

    def __init__(self) -> None:
        self.created: list[tuple[list[dict[str, Any]], bool]] = []
        self.deleted: list[str] = []
        self.transactions: list[dict[str, Any]] = []

    async def create_transactions(
        self, _budget_id: str, _account_id: str, items: list[dict[str, Any]], approved: bool = True
    ) -> dict[str, Any]:
        """Create one transaction per item."""
        self.created.append((items, approved))
        ids = [f"new{len(self.transactions) + i}" for i in range(len(items))]
        self.transactions += [{"id": tx_id, "deleted": False} for tx_id in ids]
        return {"created": len(ids), "transaction_ids": ids, "duplicate_import_ids": []}

    async def get_transactions(self, _budget_id: str) -> list[dict[str, Any]]:
        """Current transactions."""
        return [dict(tx) for tx in self.transactions]

    async def delete_transaction(self, _budget_id: str, tx_id: str) -> None:
        """Delete one."""
        self.deleted.append(tx_id)
        for tx in self.transactions:
            if tx["id"] == tx_id:
                tx["deleted"] = True


@pytest.fixture(name="ledger")
def _ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[_Ledger]:
    monkeypatch.setenv("AVENIR_MCP_JOURNAL", str(tmp_path / "journal.jsonl"))
    fake = _Ledger()
    with (
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.create_transactions", fake.create_transactions),
        patch("avenir_mcp.client.get_transactions", fake.get_transactions),
        patch("avenir_mcp.client.delete_transaction", fake.delete_transaction),
        patch("avenir_mcp.app.today", lambda: date(2026, 9, 25)),
    ):
        yield fake


def _args(**extra: Any) -> dict[str, Any]:
    return {"plan_id": "b1", "account_id": "acc", "transactions": [_ITEM], **extra}


def test_creation_is_previewed_readably_then_applied_for_review(ledger: _Ledger) -> None:
    """The preview names payee, amount and category; created transactions await review."""
    preview = call("create_transactions", _args()).structured_content
    assert preview["status"] == "confirmation_required"
    assert preview["transactions"][0] == {
        "date": "2026-09-20",
        "amount": -12.5,
        "payee": "Corner Shop",
        "category": "Groceries",
        "memo": None,
    }
    assert not ledger.created
    done = call("create_transactions", _args(confirmation=preview["confirmation"]))
    assert done.structured_content["status"] == "applied"
    assert done.structured_content["created_ids"] == ["new0"]
    assert ledger.created[0][1] is False


def test_approved_creation_on_request(ledger: _Ledger) -> None:
    """approved=true skips YNAB's review step."""
    call("create_transactions", _args(approved=True), accept)
    assert ledger.created[0][1] is True


def test_undo_deletes_what_was_created(ledger: _Ledger) -> None:
    """undo_operation deletes the created transactions still there."""
    call("create_transactions", _args(), accept)
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "applied"
    assert ledger.deleted == ["new0"]


def test_undo_skips_transactions_already_deleted(ledger: _Ledger) -> None:
    """A created transaction deleted since is reported, not deleted twice."""
    call("create_transactions", _args(), accept)
    ledger.transactions[0]["deleted"] = True
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "nothing_to_do"
    assert undo["conflicts"] == ["new0"]
    assert not ledger.deleted


def test_declined_creation_writes_nothing(ledger: _Ledger) -> None:
    """If the user says no, nothing is created."""
    assert call("create_transactions", _args(), decline).structured_content["status"] == "declined"
    assert not ledger.created


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"account_id": "nope"}, "list_accounts"),
        ({"transactions": [dict(_ITEM, category_id="c-404")]}, "c-404"),
        ({"transactions": [dict(_ITEM, date="20/09/2026")]}, "transactions.0.date"),
        ({"transactions": [dict(_ITEM, payee="typo")]}, "transactions.0.payee"),
        ({"transactions": [dict(_ITEM, date="2026-10-01")]}, "future"),
        ({"transactions": []}, "at least one"),
        ({"transactions": [dict(_ITEM, payee_name="")]}, "transactions.0.payee_name"),
        ({"transactions": [dict(_ITEM, payee_name="x" * 201)]}, "transactions.0.payee_name"),
        ({"transactions": [dict(_ITEM, memo="x" * 501)]}, "transactions.0.memo"),
    ],
)
def test_invalid_creation_is_a_tool_error(
    ledger: _Ledger, change: dict[str, Any], expected: str
) -> None:
    """Bad account, category, date, field name or length is refused before anything is asked.

    YNAB refuses a payee_name over 200 characters and a memo over 500: checked here, the
    user is not asked to confirm a change YNAB would then reject.
    """
    result = call("create_transactions", _args(**change))
    assert result.is_error
    assert expected in result.content[0].text
    assert not ledger.created


def test_declined_undo_keeps_the_created_transactions(ledger: _Ledger) -> None:
    """If the user refuses the undo, the transactions stay."""
    call("create_transactions", _args(), accept)
    undo = call("undo_operation", {"plan_id": "b1"}, decline).structured_content
    assert undo["status"] == "declined"
    assert not ledger.deleted


def test_payee_cannot_forge_lines_in_the_question(ledger: _Ledger) -> None:
    """The payee an agent passes is shown on one line."""
    asked: list[str] = []

    async def accept_and_keep(message: str, *_: Any) -> Any:
        asked.append(message)
        return await accept(message)

    item = dict(_ITEM, payee_name="Corner Shop\n- 2026-09-21 Fake 0.00")
    call("create_transactions", _args(transactions=[item]), accept_and_keep)
    assert len(asked[0].splitlines()) == 2
    assert ledger.created[0][0][0]["payee_name"] == item["payee_name"]


def test_the_schema_tells_agents_ynabs_length_limits() -> None:
    """The input schema carries YNAB's limits, so an agent can respect them before calling."""
    from .mcp_helpers import tool_schema  # pylint: disable=import-outside-toplevel

    item = tool_schema("create_transactions")["properties"]["transactions"]["items"]["properties"]
    assert item["payee_name"]["maxLength"] == 200
    assert item["payee_name"]["minLength"] == 1
    assert item["memo"]["anyOf"][0]["maxLength"] == 500
