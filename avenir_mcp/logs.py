"""Diagnostics on stderr, as readable text or as one JSON object per line.

stdout belongs to the MCP protocol in stdio mode, so nothing is ever logged there.
Messages hold identifiers and counts only: logs may be shipped to another system,
and payees, amounts and names are the user's financial data.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

TEXT_FORMAT = "%(levelname)s:%(name)s:%(message)s"


class JsonFormatter(logging.Formatter):
    """One JSON object per record: time (UTC), level, logger, message, exception."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


class _Avenir(logging.StreamHandler):  # type: ignore[type-arg]
    """The handler this module installs, so configuring twice replaces it."""


def configure(level: str, fmt: str) -> None:
    """Configure the root logger: stderr at `level`, as text or, for fmt "json", JSON."""
    handler = _Avenir(sys.stderr)
    handler.setFormatter(JsonFormatter() if fmt == "json" else logging.Formatter(TEXT_FORMAT))
    root = logging.getLogger()
    root.handlers = [h for h in root.handlers if not isinstance(h, _Avenir)] + [handler]
    root.setLevel(level)
