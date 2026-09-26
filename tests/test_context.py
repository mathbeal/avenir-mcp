"""Resources and prompts through the MCP protocol."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from avenir_mcp import server

_BUDGETS = [{"id": "b1", "name": "Personal", "last_modified_on": "2026-09-24", "extra": "x"}]
_CATS = [
    {"id": "c1", "name": "Groceries", "category_group_name": "Everyday", "budgeted": 1},
    {"id": "c2", "name": "Rent", "category_group_name": "Home", "budgeted": 1},
    {
        "id": "c3",
        "name": "Inflow: Ready to Assign",
        "category_group_name": "Internal Master Category",
    },
]
_ACCOUNTS = [
    {
        "id": "a1",
        "name": "Current account",
        "type": "checking",
        "on_budget": True,
        "closed": False,
        "balance": 12.5,
    },
    {
        "id": "a2",
        "name": "Old",
        "type": "savings",
        "on_budget": True,
        "closed": True,
        "balance": 0.0,
    },
]
PROMPTS = {"monthly_review", "classify_pending", "reconcile", "plan_next_month"}


@pytest.fixture(autouse=True, name="budget")
def _budget() -> Iterator[None]:
    with (
        patch("avenir_mcp.client.get_budgets", AsyncMock(return_value=_BUDGETS)),
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.get_accounts", AsyncMock(return_value=_ACCOUNTS)),
    ):
        yield


def _run(coro_factory: Any) -> Any:
    async def run() -> Any:
        async with Client(server.mcp) as mcp_client:
            return await coro_factory(mcp_client)

    return asyncio.run(run())


def _read(uri: str) -> str:
    contents = _run(lambda c: c.read_resource(uri))
    return str(contents[0].text)


def _tool_names() -> set[str]:
    return {t.name for t in _run(lambda c: c.list_tools())}


def _named_tools(text: str) -> set[str]:
    """Words in backticks that look like tool names."""
    return set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", text))


def test_resources_and_templates_are_listed() -> None:
    """Clients can discover what context the server offers."""
    uris = {str(r.uri) for r in _run(lambda c: c.list_resources())}
    templates = {t.uri_template for t in _run(lambda c: c.list_resource_templates())}
    assert {"ynab://budgets", "avenir-mcp://guide"} <= uris
    assert {
        "ynab://budgets/{budget_id}/categories",
        "ynab://budgets/{budget_id}/accounts",
    } <= templates


def test_budgets_resource_is_compact() -> None:
    """Only what identifies a budget."""
    assert json.loads(_read("ynab://budgets")) == [
        {"budget_id": "b1", "name": "Personal", "last_modified_on": "2026-09-24"}
    ]


def test_categories_resource_groups_assignable_categories() -> None:
    """Categories by group, internal ones left out, with the ids tools need."""
    assert json.loads(_read("ynab://budgets/b1/categories")) == [
        {"group": "Everyday", "categories": [{"category_id": "c1", "name": "Groceries"}]},
        {"group": "Home", "categories": [{"category_id": "c2", "name": "Rent"}]},
    ]


def test_accounts_resource_lists_open_accounts_in_currency() -> None:
    """Closed accounts are left out; balances are in currency units."""
    assert json.loads(_read("ynab://budgets/b1/accounts")) == [
        {
            "account_id": "a1",
            "name": "Current account",
            "type": "checking",
            "on_budget": True,
            "balance": 12.5,
        }
    ]


def test_guide_only_names_tools_that_exist() -> None:
    """The guide cannot drift from the catalog."""
    guide = _read("avenir-mcp://guide")
    named = _named_tools(guide)
    assert named, "the guide should name the tools it explains"
    assert named <= _tool_names() | PROMPTS


def test_prompts_are_listed_with_their_arguments() -> None:
    """Each workflow is a prompt the user can pick."""
    prompts = {p.name: p for p in _run(lambda c: c.list_prompts())}
    assert set(prompts) == PROMPTS
    reconcile_args = {a.name: a.required for a in prompts["reconcile"].arguments}
    assert reconcile_args == {"budget_id": True, "account_id": True, "bank_balance": True}


@pytest.mark.parametrize(
    ("name", "args", "must_name"),
    [
        ("classify_pending", {"budget_id": "b1"}, {"suggest_categories", "apply_categories"}),
        ("monthly_review", {"budget_id": "b1", "month": "2026-09-01"}, {"get_monthly_summary"}),
        (
            "reconcile",
            {"budget_id": "b1", "account_id": "a1", "bank_balance": "1234.56"},
            {"reconcile_account"},
        ),
        ("plan_next_month", {"budget_id": "b1"}, {"forecast_balance", "set_category_budget"}),
    ],
)
def test_prompts_carry_their_arguments_and_only_real_tools(
    name: str, args: dict[str, str], must_name: set[str]
) -> None:
    """A prompt fills in the user's values and names tools that exist."""
    result = _run(lambda c: c.get_prompt(name, args))
    text = "\n".join(m.content.text for m in result.messages)
    for value in args.values():
        assert value in text
    named = _named_tools(text)
    assert must_name <= named
    assert named <= _tool_names()
