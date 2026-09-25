"""Calling the server through the MCP protocol, as a client would."""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

from avenir_mcp import server


async def accept(*_: Any) -> ElicitResult[Any]:
    """A user who agrees to what the server asks."""
    return ElicitResult(action="accept", content={})


async def decline(*_: Any) -> ElicitResult[Any]:
    """A user who refuses."""
    return ElicitResult(action="decline")


def call(name: str, args: dict[str, Any], handler: Any = None) -> Any:
    """Call a tool in memory; `handler` answers elicitation, None means the client cannot."""

    async def run() -> Any:
        async with Client(server.mcp, elicitation_handler=handler) as mcp_client:
            return await mcp_client.call_tool(name, args, raise_on_error=False)

    return asyncio.run(run())
