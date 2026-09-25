"""reconcile_account through the MCP protocol: diagnose, confirm, reconcile, undo."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server

from .mcp_helpers import accept, call, decline

_ACCOUNTS = [{"id": "acc", "name": "Checking"}]
_CATS = [
    {
        "id": "c-inflow",
        "name": "Inflow: Ready to Assign",
        "category_group_name": "Internal Master Category",
    },
    {"id": "c-food", "name": "Groceries", "category_group_name": "Everyday"},
]


class _Bank:
    """A fake budget with one account."""

    def __init__(self) -> None:
        self.transactions: list[dict[str, Any]] = [
            self._tx("t1", 100000, "reconciled"),
            self._tx("t2", -30000, "cleared"),
            self._tx("t3", -5000, "uncleared"),
        ]
        self.created: list[dict[str, Any]] = []
        self.deleted: list[str] = []

    @staticmethod
    def _tx(tx_id: str, amount: int, cleared: str) -> dict[str, Any]:
        return {
            "id": tx_id,
            "amount": amount,
            "cleared": cleared,
            "account_id": "acc",
            "payee_name": "Market",
            "date": "2026-09-11",
            "deleted": False,
        }

    async def get_transactions(self, _budget_id: str) -> list[dict[str, Any]]:
        """Return copies, as YNAB would."""
        return [dict(tx) for tx in self.transactions]

    async def create_transactions(
        self, _budget_id: str, account_id: str, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Record the adjustment and add it, cleared, to the account."""
        self.created.extend(items)
        tx = self._tx("adj", round(items[0]["amount"] * 1000), "cleared")
        tx["account_id"] = account_id
        self.transactions.append(tx)
        return {"created": 1, "transaction_ids": ["adj"], "duplicate_import_ids": []}

    async def set_transactions_cleared(
        self, _budget_id: str, tx_ids: list[str], cleared: str
    ) -> list[str]:
        """Apply a cleared status."""
        for tx in self.transactions:
            if tx["id"] in tx_ids:
                tx["cleared"] = cleared
        return tx_ids

    async def delete_transaction(self, _budget_id: str, tx_id: str) -> None:
        """Mark a transaction deleted."""
        self.deleted.append(tx_id)
        for tx in self.transactions:
            if tx["id"] == tx_id:
                tx["deleted"] = True

    def status(self, tx_id: str) -> str:
        """Current cleared status of a transaction."""
        return str(next(tx["cleared"] for tx in self.transactions if tx["id"] == tx_id))


@pytest.fixture(name="bank")
def _bank(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[_Bank]:
    monkeypatch.setenv("AVENIR_MCP_JOURNAL", str(tmp_path / "journal.jsonl"))
    fake = _Bank()
    with (
        patch("avenir_mcp.client.get_transactions", fake.get_transactions),
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.create_transactions", fake.create_transactions),
        patch("avenir_mcp.client.set_transactions_cleared", fake.set_transactions_cleared),
        patch("avenir_mcp.client.delete_transaction", fake.delete_transaction),
    ):
        yield fake


def _args(balance: float, **extra: Any) -> dict[str, Any]:
    return {"budget_id": "b1", "account_id": "acc", "bank_balance": balance, **extra}


def test_reconcile_declares_a_write() -> None:
    """It can change the account: clients must know."""

    async def run() -> Any:
        async with Client(server.mcp) as mcp_client:
            return next(t for t in await mcp_client.list_tools() if t.name == "reconcile_account")

    annotations = asyncio.run(run()).annotations
    assert annotations.read_only_hint is False
    assert annotations.destructive_hint is True


def test_difference_is_diagnosed_without_writing(bank: _Bank) -> None:
    """A gap is explained, not silently adjusted: nothing is asked or written."""
    data = call("reconcile_account", _args(65.0), accept).structured_content
    assert data["status"] == "difference_found"
    assert data["analysis"]["difference"] == -5.0
    assert data["analysis"]["explained_by"] == ["t3"]
    assert "adjust" in data["message"]
    assert bank.status("t2") == "cleared" and not bank.created


def test_matching_balance_reconciles_after_confirmation(bank: _Bank) -> None:
    """Balance matches: cleared transactions become reconciled once the code is given."""
    preview = call("reconcile_account", _args(70.0)).structured_content
    assert preview["status"] == "confirmation_required"
    assert bank.status("t2") == "cleared"
    code = preview["confirmation"]
    data = call("reconcile_account", _args(70.0, confirmation=code)).structured_content
    assert data["status"] == "applied"
    assert bank.status("t2") == "reconciled"
    assert bank.status("t3") == "uncleared"


def test_adjustment_is_created_on_request_then_undone(bank: _Bank) -> None:
    """adjust=true records the gap as a Ready to Assign adjustment; undo removes it."""
    data = call("reconcile_account", _args(80.0, adjust=True), accept).structured_content
    assert data["status"] == "applied"
    assert data["adjustment"] == 10.0
    assert bank.created[0]["amount"] == 10.0
    assert bank.created[0]["category_id"] == "c-inflow"
    assert bank.status("adj") == "reconciled"
    undo = call("undo_operation", {"budget_id": "b1"}, accept).structured_content
    assert undo["status"] == "applied"
    assert bank.deleted == ["adj"]
    assert bank.status("t2") == "cleared"


def test_nothing_to_reconcile(bank: _Bank) -> None:
    """Already reconciled and matching: nothing to do."""
    bank.transactions = [bank.transactions[0]]
    data = call("reconcile_account", _args(100.0)).structured_content
    assert data["status"] == "nothing_to_do"


def test_unknown_account_is_a_tool_error(bank: _Bank) -> None:
    """An account id that is not in the budget is refused, saying where to find one."""
    result = call("reconcile_account", {**_args(1.0), "account_id": "nope"})
    assert result.is_error
    assert "list_accounts" in result.content[0].text
    assert not bank.created


def test_declined_reconciliation_changes_nothing(bank: _Bank) -> None:
    """If the user says no, statuses stay as they are."""

    data = call("reconcile_account", _args(70.0), decline).structured_content
    assert data["status"] == "declined"
    assert bank.status("t2") == "cleared"


def test_undo_reconcile_without_elicitation_needs_the_code(bank: _Bank) -> None:
    """Undoing a reconciliation is previewed and confirmed like any write."""
    call("reconcile_account", _args(70.0), accept)
    preview = call("undo_operation", {"budget_id": "b1"}).structured_content
    assert preview["status"] == "confirmation_required"
    assert bank.status("t2") == "reconciled"
    code = preview["confirmation"]
    data = call("undo_operation", {"budget_id": "b1", "confirmation": code}).structured_content
    assert data["status"] == "applied"
    assert bank.status("t2") == "cleared"


def test_declined_undo_of_a_reconciliation_changes_nothing(bank: _Bank) -> None:
    """If the user refuses the undo, the account stays reconciled."""

    call("reconcile_account", _args(70.0), accept)
    data = call("undo_operation", {"budget_id": "b1"}, decline).structured_content
    assert data["status"] == "declined"
    assert bank.status("t2") == "reconciled"
