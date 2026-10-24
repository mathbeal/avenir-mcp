# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Run the real avenir-mcp server with its clock pinned to the demo plan's day.

Only the evaluation starts the server this way, in place of the `avenir-mcp` command: a
client never sees a configuration flag for this, since freezing the clock has no use
outside the invented demo plan. See the documentation generator's `on_demo_plan`, which
pins the same day for an in-process client instead of a subprocess.
"""

from __future__ import annotations

from unittest.mock import patch

from evals import demo_budget


def main() -> None:
    """Patch `avenir_mcp.app.today` to the demo plan's day, then run the real server."""
    with patch("avenir_mcp.app.today", lambda: demo_budget.TODAY):
        from avenir_mcp.server import main as run_server  # pylint: disable=import-outside-toplevel

        run_server()


if __name__ == "__main__":
    main()
