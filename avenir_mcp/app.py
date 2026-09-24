"""The MCP server instance and what decides which tools it exposes."""

from __future__ import annotations

from datetime import date

from fastmcp import FastMCP  # pylint: disable=import-error

mcp = FastMCP("avenir")


# Tools that change the budget carry this tag; read-only mode hides them.
WRITE_TAG = "write"


def configure(enable_writes: bool) -> None:
    """Expose write tools only when enabled; otherwise they are neither listed nor callable."""
    if enable_writes:
        mcp.enable(tags={WRITE_TAG})
    else:
        mcp.disable(tags={WRITE_TAG})


def today() -> date:
    """Today's date; a function so tests can fix it."""
    return date.today()
