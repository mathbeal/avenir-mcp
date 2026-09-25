"""Diagnostics stay short, on stderr, and quiet by default."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastmcp.exceptions import ToolError

from avenir_mcp import app, server


def _record(error: BaseException) -> logging.LogRecord:
    """A log record as FastMCP writes it with logger.exception()."""
    return logging.LogRecord(
        "fastmcp.server.server",
        logging.ERROR,
        __file__,
        1,
        "Error calling tool 'x'",
        None,
        (type(error), error, None),
    )


def test_expected_tool_errors_are_logged_on_one_line() -> None:
    """A ToolError is a message for the agent, not a crash: no traceback."""
    record = _record(ToolError("month must be YYYY-MM-01"))
    assert app.QuietToolErrors().filter(record) is True
    assert record.exc_info is None
    assert record.getMessage() == "Error calling tool 'x': month must be YYYY-MM-01"


def test_unexpected_errors_keep_their_traceback() -> None:
    """A real failure keeps everything needed to debug it."""
    record = _record(ValueError("boom"))
    assert app.QuietToolErrors().filter(record) is True
    assert record.exc_info is not None


def test_filter_is_installed_on_fastmcp_tool_logger() -> None:
    """The filter sits where FastMCP logs tool errors."""
    filters = logging.getLogger("fastmcp.server.server").filters
    assert any(isinstance(f, app.QuietToolErrors) for f in filters)


@pytest.fixture(name="root_level")
def _root_level() -> Iterator[None]:
    before = logging.getLogger().level
    yield
    logging.getLogger().setLevel(before)


@pytest.mark.usefixtures("root_level")
@pytest.mark.parametrize(("value", "expected"), [(None, logging.WARNING), ("DEBUG", logging.DEBUG)])
def test_log_level_is_warning_unless_configured(
    monkeypatch: pytest.MonkeyPatch, value: str | None, expected: int
) -> None:
    """Routine calls are not logged unless AVENIR_MCP_LOG_LEVEL asks for it."""
    if value is None:
        monkeypatch.delenv("AVENIR_MCP_LOG_LEVEL", raising=False)
    else:
        monkeypatch.setenv("AVENIR_MCP_LOG_LEVEL", value)
    with patch.object(server.mcp, "run"):
        server.main()
    assert logging.getLogger().level == expected
