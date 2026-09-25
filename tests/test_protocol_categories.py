"""update_category through the MCP protocol: preview, confirmation, then the change."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

from avenir_mcp import server

_CATS = [
    {
        "id": "c-pharma",
        "name": "Drugstore",
        "category_group_id": "g-health",
        "category_group_name": "Health",
    },
    {
        "id": "c-child",
        "name": "Childcare",
        "category_group_id": "g-care",
        "category_group_name": "Care",
    },
]
_GROUPS = [{"id": "g-health", "name": "Health"}, {"id": "g-care", "name": "Care"}]


@pytest.fixture(name="update")
def _update() -> Iterator[AsyncMock]:
    updated = AsyncMock(return_value={})
    with (
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.get_category_groups", AsyncMock(return_value=_GROUPS)),
        patch("avenir_mcp.client.update_category", updated),
    ):
        yield updated


async def _accept(*_: Any) -> ElicitResult[Any]:
    return ElicitResult(action="accept", content={})


def _call(args: dict[str, Any], handler: Any = None) -> Any:
    async def run() -> Any:
        async with Client(server.mcp, elicitation_handler=handler) as mcp_client:
            return await mcp_client.call_tool("update_category", args, raise_on_error=False)

    return asyncio.run(run())


def test_update_category_declares_a_reversible_write() -> None:
    """Clients see a write that overwrites a name, safe to repeat."""

    async def run() -> Any:
        async with Client(server.mcp) as mcp_client:
            return next(t for t in await mcp_client.list_tools() if t.name == "update_category")

    annotations = asyncio.run(run()).annotations
    assert annotations.readOnlyHint is False
    assert annotations.destructiveHint is True
    assert annotations.idempotentHint is True


def test_rename_is_previewed_then_applied_with_the_code(update: AsyncMock) -> None:
    """Without elicitation the first call previews; the code applies the rename only."""
    args = {"budget_id": "b1", "category_id": "c-pharma", "name": "Pharmacy"}
    preview = _call(args).structured_content
    assert preview["status"] == "confirmation_required"
    assert (preview["from_name"], preview["to_name"]) == ("Drugstore", "Pharmacy")
    update.assert_not_awaited()
    done = _call({**args, "confirmation": preview["confirmation"]}).structured_content
    assert done["status"] == "applied"
    update.assert_awaited_once_with("b1", "c-pharma", name="Pharmacy", category_group_id=None)


def test_move_to_another_group_after_elicitation(update: AsyncMock) -> None:
    """Moving names the groups before and after, and sends only the group."""
    data = _call(
        {"budget_id": "b1", "category_id": "c-child", "category_group_id": "g-health"}, _accept
    ).structured_content
    assert data["status"] == "applied"
    assert (data["from_group"], data["to_group"]) == ("Care", "Health")
    update.assert_awaited_once_with("b1", "c-child", name=None, category_group_id="g-health")
    assert "update_category" in data["message"]


def test_nothing_to_change_writes_nothing(update: AsyncMock) -> None:
    """Same name and same group: no question, no write."""
    data = _call(
        {"budget_id": "b1", "category_id": "c-pharma", "name": "Drugstore"}
    ).structured_content
    assert data["status"] == "nothing_to_do"
    update.assert_not_awaited()


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"category_id": "c-404", "name": "X"}, "c-404"),
        ({"category_id": "c-pharma", "category_group_id": "g-404"}, "g-404"),
        ({"category_id": "c-pharma", "name": "  "}, "empty"),
    ],
)
def test_invalid_update_is_a_tool_error(
    update: AsyncMock, args: dict[str, Any], expected: str
) -> None:
    """Unknown category or group, or a blank name, is refused before anything is asked."""
    result = _call({"budget_id": "b1", **args})
    assert result.is_error
    assert expected in result.content[0].text
    update.assert_not_awaited()


def test_declined_update_changes_nothing(update: AsyncMock) -> None:
    """If the user says no, the category stays as it is."""

    async def decline(*_: Any) -> ElicitResult[Any]:
        return ElicitResult(action="decline")

    data = _call(
        {"budget_id": "b1", "category_id": "c-pharma", "name": "Pharmacy"}, decline
    ).structured_content
    assert data["status"] == "declined"
    update.assert_not_awaited()


# ---------------------------------------------------------------------------
# create_category
# ---------------------------------------------------------------------------


@pytest.fixture(name="create")
def _create() -> Iterator[AsyncMock]:
    created = AsyncMock(return_value={"id": "c-new", "name": "Gym"})
    with (
        patch("avenir_mcp.client.get_categories", AsyncMock(return_value=_CATS)),
        patch("avenir_mcp.client.get_category_groups", AsyncMock(return_value=_GROUPS)),
        patch("avenir_mcp.client.create_category", created),
    ):
        yield created


def _create_call(args: dict[str, Any], handler: Any = None) -> Any:
    async def run() -> Any:
        async with Client(server.mcp, elicitation_handler=handler) as mcp_client:
            return await mcp_client.call_tool("create_category", args, raise_on_error=False)

    return asyncio.run(run())


_NEW = {"budget_id": "b1", "category_group_id": "g-health", "name": "Gym"}


def test_new_category_is_previewed_then_created_with_the_code(create: AsyncMock) -> None:
    """The preview names the group; the code creates it and returns its id."""
    preview = _create_call(_NEW).structured_content
    assert preview["status"] == "confirmation_required"
    assert (preview["name"], preview["group"]) == ("Gym", "Health")
    create.assert_not_awaited()
    done = _create_call({**_NEW, "confirmation": preview["confirmation"]}).structured_content
    assert done["status"] == "applied"
    assert done["category_id"] == "c-new"
    create.assert_awaited_once_with("b1", "g-health", "Gym")


def test_declined_category_is_not_created(create: AsyncMock) -> None:
    """If the user says no, nothing is created."""

    async def decline(*_: Any) -> ElicitResult[Any]:
        return ElicitResult(action="decline")

    assert _create_call(_NEW, decline).structured_content["status"] == "declined"
    create.assert_not_awaited()


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"category_group_id": "g-404"}, "list_category_groups"),
        ({"name": " "}, "empty"),
        ({"name": "drugstore"}, "already"),
    ],
)
def test_invalid_new_category_is_a_tool_error(
    create: AsyncMock, change: dict[str, Any], expected: str
) -> None:
    """Unknown group, blank name or a name already in the group is refused."""
    result = _create_call({**_NEW, **change})
    assert result.is_error
    assert expected in result.content[0].text
    create.assert_not_awaited()
