"""The MCP server instance and what decides which tools it exposes."""

from __future__ import annotations

import re
from datetime import date

from fastmcp import FastMCP  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error

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


_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-01$")


def check_month(month: str) -> None:
    """Refuse a malformed month before YNAB answers with a bare 404."""
    if month != "current" and not _MONTH.match(month):
        raise ToolError(
            f"month must be 'current' or the first day of a month as YYYY-MM-01, got {month!r}."
        )


def resolve_month(month: str) -> str:
    """The actual YYYY-MM-01 for 'current', so a journaled change names its month."""
    return f"{today():%Y-%m}-01" if month == "current" else month
