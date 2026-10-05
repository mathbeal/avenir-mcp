# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What the client asks YNAB to read a plan's payees, and to rename one."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

from avenir_mcp import client


def test_payees_are_read_from_the_plan_as_ynab_holds_them() -> None:
    """One GET on the plan's payees; the client filters nothing out."""
    payees: list[dict[str, Any]] = [
        {"id": "p1", "name": "RAIL CO", "transfer_account_id": None, "deleted": False},
        {"id": "p2", "name": "OLD SHOP", "transfer_account_id": None, "deleted": True},
    ]
    get = AsyncMock(return_value={"data": {"payees": payees}})
    with patch("avenir_mcp.client._get", get):
        found = asyncio.run(client.get_payees("b1"))
    assert found == payees
    assert get.call_args.args == ("/plans/b1/payees",)


def test_renaming_a_payee_patches_that_payee_with_its_new_name() -> None:
    """The rename goes in one PATCH of the payee, and only the name is sent."""
    patched = AsyncMock(return_value={"data": {"payee": {"id": "p1", "name": "Rail Co"}}})
    with patch("avenir_mcp.client._patch", patched):
        done = asyncio.run(client.rename_payee("b1", "p1", "Rail Co"))
    assert patched.call_args.args == (
        "/plans/b1/payees/p1",
        {"payee": {"name": "Rail Co"}},
    )
    assert done == {"id": "p1", "name": "Rail Co"}
