"""Calling the server through the MCP protocol, as a client would."""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

from avenir_mcp import server


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
