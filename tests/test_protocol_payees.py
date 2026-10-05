# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""list_payees and rename_payee through the MCP protocol: list, preview, confirm, undo."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from .mcp_helpers import FLAT, FORGED, accept, asking, call, decline, one_line, tool_schema

_LABEL = "CB MARKET FRESH FACT 050926 525130******1"


class FakePayees:
    """The payees and transactions of a plan, and the renames YNAB was asked for."""

    def __init__(self) -> None:
        """Two labels of one shop, a direct debit, a transfer and a deleted payee."""
        self.names: dict[str, str] = {
            "p-fresh": _LABEL,
            "p-rail": "RAIL CO",
            "p-transfer": "Transfer : Savings",
            "p-gone": "OLD SHOP",
            "p-forged": FORGED,
        }
        self.sent: list[tuple[str, str]] = []

    async def get_payees(self, _plan_id: str) -> list[dict[str, Any]]:
        """The payees, as YNAB returns them."""
        return [
            {
                "id": payee_id,
                "name": name,
                "transfer_account_id": "acc-savings" if payee_id == "p-transfer" else None,
                "deleted": payee_id == "p-gone",
            }
            for payee_id, name in self.names.items()
        ]

    async def get_transactions(self, _plan_id: str, **_: Any) -> list[dict[str, Any]]:
        """Three transactions on the direct debit, one on the card label."""
        rows = [("p-fresh", "2026-09-05"), ("p-rail", "2026-07-18"), ("p-rail", "2026-08-18")]
        rows.append(("p-rail", "2026-09-18"))
        return [
            {
                "id": f"tx-{i}",
                "date": date,
                "amount": -12340,
                "payee_id": payee_id,
                "payee_name": self.names[payee_id],
                "deleted": False,
            }
            for i, (payee_id, date) in enumerate(rows)
        ]

    async def rename_payee(self, _plan_id: str, payee_id: str, name: str) -> dict[str, Any]:
        """Record and apply the rename."""
        self.sent.append((payee_id, name))
        self.names[payee_id] = name
        return {"id": payee_id, "name": name}


@pytest.fixture(name="ynab")
def _ynab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakePayees]:
    fake = FakePayees()
    monkeypatch.setenv("AVENIR_MCP_JOURNAL", str(tmp_path / "journal.jsonl"))
    with (
        patch("avenir_mcp.client.get_payees", fake.get_payees),
        patch("avenir_mcp.client.get_transactions", fake.get_transactions),
        patch("avenir_mcp.client.rename_payee", fake.rename_payee),
    ):
        yield fake


def _args(**extra: Any) -> dict[str, Any]:
    return {"plan_id": "b1", "payee_id": "p-fresh", "name": "Market Fresh", **extra}


def test_the_payees_come_back_with_their_merchant_and_their_use(ynab: FakePayees) -> None:
    """Each payee says how often it is used and which merchant its label names."""
    listed = call("list_payees", {"plan_id": "b1"}).structured_content
    assert (listed["total"], listed["shown"]) == (3, 3)
    assert listed["payees"][0] == {
        "payee_id": "p-rail",
        "name": "RAIL CO",
        "merchant": "RAIL CO",
        "transactions": 3,
        "last_date": "2026-09-18",
    }
    assert [p["payee_id"] for p in listed["payees"]][1] == "p-fresh"
    assert ynab.sent == []


def test_listing_leaves_out_what_cannot_be_renamed(ynab: FakePayees) -> None:
    """A transfer's payee belongs to its account, and a deleted payee is gone."""
    listed = call("list_payees", {"plan_id": "b1"}).structured_content
    assert {p["payee_id"] for p in listed["payees"]} == {"p-rail", "p-fresh", "p-forged"}
    assert ynab.sent == []


def test_a_label_written_to_forge_a_line_is_listed_on_one_line(ynab: FakePayees) -> None:
    """A payee name with a line break cannot add a line to what the agent relays."""
    listed = call("list_payees", {"plan_id": "b1"}).structured_content
    forged = next(p for p in listed["payees"] if p["payee_id"] == "p-forged")
    assert forged["name"] == FLAT
    assert ynab.sent == []


def test_a_search_finds_the_labels_of_one_shop(ynab: FakePayees) -> None:
    """Searching by the merchant's name finds the label the bank wrote, whatever the case."""
    listed = call("list_payees", {"plan_id": "b1", "search": "market fresh"}).structured_content
    assert [p["payee_id"] for p in listed["payees"]] == ["p-fresh"]
    assert ynab.sent == []


def test_the_limit_is_bounded_by_what_an_answer_can_carry(ynab: FakePayees) -> None:
    """The schema states the bounds, so an agent cannot ask for thousands of payees."""
    limit = tool_schema("list_payees")["properties"]["limit"]
    assert (limit["minimum"], limit["maximum"]) == (1, 200)
    assert ynab.sent == []


def test_the_preview_names_the_label_the_merchant_and_the_history(ynab: FakePayees) -> None:
    """Without elicitation: the names before and after, a code, and nothing renamed."""
    preview = call("rename_payee", _args()).structured_content
    assert preview["status"] == "confirmation_required"
    assert (preview["from_name"], preview["to_name"]) == (_LABEL, "Market Fresh")
    assert preview["transactions"] == 1
    assert preview["confirmation"]
    assert ynab.sent == []


def test_the_code_applies_the_rename(ynab: FakePayees) -> None:
    """With the code, YNAB is asked once, and the result names the operation to undo."""
    code = call("rename_payee", _args()).structured_content["confirmation"]
    done = call("rename_payee", _args(confirmation=code)).structured_content
    assert done["status"] == "applied"
    assert done["operation_id"]
    assert ynab.sent == [("p-fresh", "Market Fresh")]


def test_the_user_is_asked_one_readable_question(ynab: FakePayees) -> None:
    """The question names both names on one line, and how much history is affected."""
    asked: list[str] = []
    call("rename_payee", _args(), asking(asked))
    assert asked == [f"Rename payee '{_LABEL}' to 'Market Fresh'? 1 transaction(s) name it."]
    assert ynab.sent == [("p-fresh", "Market Fresh")]


def test_a_forged_label_stays_inside_its_line_of_the_question(ynab: FakePayees) -> None:
    """A payee name with a line break cannot forge a line of the question."""
    asked: list[str] = []
    call("rename_payee", _args(payee_id="p-forged", name="Rent"), asking(asked))
    assert one_line(asked[0])
    assert ynab.sent == [("p-forged", "Rent")]


def test_the_name_it_already_has_changes_nothing(ynab: FakePayees) -> None:
    """Asked for the current name, nothing is asked of the user nor of YNAB."""
    result = call("rename_payee", _args(name=f"  {_LABEL}  "), accept).structured_content
    assert result["status"] == "nothing_to_do"
    assert ynab.sent == []


def test_a_declined_rename_changes_nothing(ynab: FakePayees) -> None:
    """If the user says no, the payee keeps its name."""
    result = call("rename_payee", _args(), decline).structured_content
    assert result["status"] == "declined"
    assert ynab.sent == []


def test_the_journal_keeps_the_two_names_and_nothing_else(ynab: FakePayees, tmp_path: Path) -> None:
    """Undoing a rename needs the previous name: the line holds it, and no transaction."""
    call("rename_payee", _args(), accept)
    line = json.loads((tmp_path / "journal.jsonl").read_text(encoding="utf-8"))
    assert line["kind"] == "payee"
    assert line["details"] == {
        "payee_id": "p-fresh",
        "from": _LABEL,
        "to": "Market Fresh",
    }
    assert line["moves"] == []
    assert ynab.sent == [("p-fresh", "Market Fresh")]


def test_undo_puts_the_previous_name_back(ynab: FakePayees) -> None:
    """undo_operation renames the payee to the label the bank gave it."""
    call("rename_payee", _args(), accept)
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "applied"
    assert ynab.names["p-fresh"] == _LABEL
    assert ynab.sent[-1] == ("p-fresh", _LABEL)


def test_undo_asks_before_renaming_back(ynab: FakePayees) -> None:
    """The undo is confirmed too, naming the name it would restore."""
    call("rename_payee", _args(), accept)
    asked: list[str] = []
    call("undo_operation", {"plan_id": "b1"}, asking(asked))
    assert asked[-1] == f"Undo: name the payee '{_LABEL}' again?"
    assert ynab.names["p-fresh"] == _LABEL


def test_undo_leaves_a_payee_renamed_since_alone(ynab: FakePayees) -> None:
    """A payee renamed again, in YNAB or here, is not overwritten but reported."""
    call("rename_payee", _args(), accept)
    ynab.names["p-fresh"] = "Fresh Market"
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "nothing_to_do"
    assert undo["conflicts"] == ["p-fresh"]
    assert ynab.names["p-fresh"] == "Fresh Market"
    assert len(ynab.sent) == 1


def test_undo_of_a_payee_deleted_since_does_nothing(ynab: FakePayees) -> None:
    """A payee YNAB no longer returns is left alone instead of being created again."""
    call("rename_payee", _args(), accept)
    del ynab.names["p-fresh"]
    undo = call("undo_operation", {"plan_id": "b1"}, accept).structured_content
    assert undo["status"] == "nothing_to_do"
    assert undo["conflicts"] == ["p-fresh"]
    assert len(ynab.sent) == 1


def test_the_schema_tells_agents_the_length_ynab_accepts(ynab: FakePayees) -> None:
    """YNAB refuses a payee name over 500 characters: the parameter says so."""
    name = tool_schema("rename_payee")["properties"]["name"]
    assert (name["minLength"], name["maxLength"]) == (1, 500)
    assert ynab.sent == []


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"payee_id": "p-404"}, "p-404"),
        ({"payee_id": "p-gone"}, "p-gone"),
        ({"payee_id": "p-transfer"}, "transfer"),
        ({"name": "   "}, "empty"),
        ({"name": "Market\nFresh"}, "line break"),
        ({"name": "RAIL CO"}, "already the name"),
        ({"name": "Market\x00Fresh"}, "NUL"),
        ({"name": "M" * 501}, "at most 500"),
        ({"name": ""}, "at least 1"),
    ],
)
def test_what_ynab_or_the_user_could_not_use_is_refused_before_asking(
    ynab: FakePayees, args: dict[str, Any], expected: str
) -> None:
    """An unknown, deleted or transfer payee, or a name YNAB or the user could not read."""
    result = call("rename_payee", _args(**args), accept)
    assert result.is_error
    assert expected in result.content[0].text
    assert ynab.sent == []
