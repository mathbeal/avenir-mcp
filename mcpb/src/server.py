#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What Claude Desktop starts when the extension of this directory is installed.

Claude Desktop resolves `pyproject.toml` with its own uv and its own Python, then runs
this file. It has no behaviour of its own: it turns the extension's settings into the
environment avenir-mcp reads, then runs the server over stdio, as any other client does.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from avenir_mcp import server

if TYPE_CHECKING:
    from collections.abc import MutableMapping

# Claude Desktop writes a checkbox as the JSON value behind it, `true` or `false`, while
# AVENIR_MCP_WRITE registers the write tools on exactly `1`. These spellings are read as
# a tick; anything else, an empty value included, leaves the server read-only.
TICKED = frozenset({"true", "1", "yes", "on"})


def enable_writes(environment: MutableMapping[str, str]) -> None:
    """Turn the "Allow changes to your plans" setting into the value the server reads.

    Args:
        environment: The environment avenir-mcp will read; changed in place.
    """
    if environment.get("AVENIR_MCP_WRITE", "").strip().lower() in TICKED:
        environment["AVENIR_MCP_WRITE"] = "1"


def main() -> None:
    """Translate the extension's settings, then run avenir-mcp."""
    enable_writes(os.environ)
    # No argument: `--version` belongs to the command line, and the server's
    # configuration is in the environment.
    server.main([])


if __name__ == "__main__":
    main()
