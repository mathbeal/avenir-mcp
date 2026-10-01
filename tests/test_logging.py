# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Diagnostics stay short, on stderr, and quiet by default."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import ToolError

from avenir_mcp import app, classifier, client, server


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


def test_logs_hold_no_financial_data(caplog: pytest.LogCaptureFixture) -> None:
    """Logs may be shipped elsewhere: payees, amounts and names stay out of them."""
    categories = [{"id": "c1", "name": "Pets"}, {"id": "c2", "name": "Books"}]
    history = {
        "SECRET SHOP": {"c1": 9, "c2": 1},
        "HIDDEN CAFE": {"c1": 1, "c2": 1},
    }
    caplog.set_level(logging.DEBUG, logger="avenir_mcp")
    for payee in ("CB SECRET SHOP 12/09", "HIDDEN CAFE", "NEVER SEEN"):
        classifier.score_payee(payee, history, categories)
    with (
        patch("avenir_mcp.client._patch", AsyncMock(return_value={"data": {"category": {}}})),
        patch("avenir_mcp.client._post", AsyncMock(return_value={"data": {"category": {}}})),
    ):
        asyncio.run(client.set_category_budgeted("b1", "2026-09-01", "c1", 1234.56))
        asyncio.run(client.create_category("b1", "g1", "Pets"))
    assert caplog.records
    for secret in ("SECRET", "HIDDEN", "NEVER", "1234", "Pets", "Books"):
        assert secret not in caplog.text


@pytest.fixture(name="restore_root")
def _restore_root() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers, root.level = handlers, level


@pytest.mark.usefixtures("restore_root")
def test_json_logs_are_one_object_per_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AVENIR_MCP_LOG_FORMAT=json: one JSON object per line, ready for a log collector."""
    monkeypatch.setenv("AVENIR_MCP_LOG_FORMAT", "json")
    monkeypatch.setenv("AVENIR_MCP_LOG_LEVEL", "INFO")
    with patch.object(server.mcp, "run"):
        server.main([])
    logger = logging.getLogger("avenir_mcp.test")
    logger.info("Fetching %s", "accounts")
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logger.exception("Failed")
    lines = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    assert lines[0]["level"] == "INFO"
    assert lines[0]["logger"] == "avenir_mcp.test"
    assert lines[0]["message"] == "Fetching accounts"
    assert lines[0]["time"].endswith("+00:00")
    assert "RuntimeError: boom" in lines[1]["exception"]


@pytest.mark.usefixtures("restore_root")
def test_text_logs_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without the variable, logs stay one readable line each."""
    monkeypatch.delenv("AVENIR_MCP_LOG_FORMAT", raising=False)
    monkeypatch.setenv("AVENIR_MCP_LOG_LEVEL", "INFO")
    with patch.object(server.mcp, "run"):
        server.main([])
    logging.getLogger("avenir_mcp.test").info("Fetching accounts")
    assert capsys.readouterr().err.strip() == "INFO:avenir_mcp.test:Fetching accounts"
