# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""A tool that reaches a non-GET operation of YNAB carries the write tag, and no other tool does.

tests/test_policy.py only checks the tag against the annotation written by hand on the same
decorator: both could be wrong together. This ties the tag to what the code actually calls,
following docsgen.api's own map from a tool down to the YNAB operations it reaches.
"""

from __future__ import annotations

import asyncio

from avenir_mcp import server
from docsgen import api


def test_exactly_the_tools_that_send_a_write_to_ynab_carry_the_write_tag() -> None:
    """Every tool behind a non-GET operation is tagged; every tagged tool is behind one."""
    users, unknown = api.used()
    assert not unknown
    ops = {op["id"]: op for op in api.snapshot()["operations"]}
    writers = {
        user for key, names in users.items() if ops[key]["method"] != "GET" for user in names
    }
    server.configure(enable_writes=True)
    tools = asyncio.run(server.mcp.list_tools())
    tagged = {tool.name for tool in tools if server.WRITE_TAG in tool.tags}
    assert writers == tagged
