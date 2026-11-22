# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Calling the server through the MCP protocol, as a client would."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from fastmcp.server.elicitation import AcceptedElicitation

from avenir_mcp import server, tools_undo


async def accept(*_: Any) -> ElicitResult[Any]:
    """A user who agrees to what the server asks."""
    return ElicitResult(action="accept", content={"value": True})


async def decline(*_: Any) -> ElicitResult[Any]:
    """A user who refuses."""
    return ElicitResult(action="decline")


def call(name: str, args: dict[str, Any], handler: Any = None) -> Any:
    """Call a tool in memory; `handler` answers elicitation, None means the client cannot."""

    async def run() -> Any:
        async with Client(server.mcp, elicitation_handler=handler) as mcp_client:
            return await mcp_client.call_tool(name, args, raise_on_error=False)

    return asyncio.run(run())


def tool_schema(name: str) -> dict[str, Any]:
    """The input schema a client sees for a tool."""

    async def run() -> dict[str, Any]:
        async with Client(server.mcp) as mcp_client:
            tools = {tool.name: tool for tool in await mcp_client.list_tools()}
            schema: dict[str, Any] = tools[name].input_schema
            return schema

    return asyncio.run(run())


# A name with a line break, written to add a line of its own to a confirmation question.
FORGED = "Rent\n- 2026-09-03 Fake 0.00: forged"
# The same name once made safe to show: one line.
FLAT = "Rent - 2026-09-03 Fake 0.00: forged"


def asking(asked: list[str]) -> Any:
    """A user who agrees, and the questions put to them, recorded in `asked`."""

    async def handler(message: str, *_: Any) -> ElicitResult[Any]:
        asked.append(message)
        return ElicitResult(action="accept", content={"value": True})

    return handler


def one_line(question: str) -> bool:
    """Whether the forged name stayed inside its line of the question."""
    return FLAT in question and "\n- 2026-09-03 Fake" not in question


@dataclass
class _Session:
    def check_client_capability(self, _capability: Any) -> bool:
        """A client that can always ask."""
        return True


@dataclass
class _RequestContext:
    protocol_version: str


@dataclass
class OldProtocolContext:
    """A fake Context whose elicitation blocks synchronously, as before 2026-07-28.

    Calls a tool directly (not through a Client), to make something happen between the
    state read before asking and the write after: the gap this codebase calls the old
    protocol's "no limit on how long the question stays open".
    """

    on_elicit: Callable[[], None] = lambda: None
    protocol_version: str = "2025-06-18"
    session: _Session = field(default_factory=_Session)

    @property
    def request_context(self) -> _RequestContext:
        """The negotiated protocol version."""
        return _RequestContext(self.protocol_version)

    async def elicit(self, _question: str, _response_type: type) -> Any:
        """Run the side effect, then answer yes, as a user would after a long wait."""
        self.on_elicit()
        return AcceptedElicitation(data=True)


def undo_through_a_blocking_drift(drift: Callable[[], None]) -> Any:
    """Undo plan b1 directly, as the old protocol would once a blocking question is answered.

    `drift` runs as the side effect of saying yes, standing in for a change made in YNAB
    while the question was still open.

    Args:
        drift: What to do once the question is answered, before the write.

    Returns:
        What undo_operation returns.
    """
    return asyncio.run(tools_undo.undo_operation("b1", OldProtocolContext(on_elicit=drift)))  # type: ignore[arg-type]
