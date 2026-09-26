"""The MCP server instance and what decides which tools it exposes."""

from __future__ import annotations

import logging
import re
from datetime import date

from fastmcp import FastMCP  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error

mcp = FastMCP("avenir-mcp")


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


class QuietToolErrors(logging.Filter):  # pylint: disable=too-few-public-methods
    """Log an expected ToolError on one line; keep tracebacks for real failures.

    FastMCP logs every tool error with its traceback. A ToolError is a message
    written for the agent (a malformed month, an unknown account), not a crash.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info and isinstance(record.exc_info[1], ToolError):
            record.msg = f"{record.getMessage()}: {record.exc_info[1]}"
            record.args = None
            record.exc_info = None
            record.exc_text = None
        return True


logging.getLogger("fastmcp.server.server").addFilter(QuietToolErrors())
