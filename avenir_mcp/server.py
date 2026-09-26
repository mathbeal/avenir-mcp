"""Entry point of the avenir-mcp MCP server.

Importing the tool modules registers their tools on the shared server instance.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from pydantic import SecretStr  # pylint: disable=import-error

from avenir_mcp import (  # noqa: F401  pylint: disable=unused-import
    __version__,
    context,
    http_auth,
    logs,
    tools_accounts,
    tools_categories,
    tools_classify,
    tools_undo,
)
from avenir_mcp.app import WRITE_TAG, configure, mcp, today
from avenir_mcp.tools_accounts import create_transactions
from avenir_mcp.tools_budget import (
    approve_transactions,
    find_transactions,
    get_budget_vs_actual,
    get_category_balances,
    get_monthly_summary,
    get_spending_trends,
    list_accounts,
    list_category_groups,
    list_plans,
    list_scheduled_transactions,
)
from avenir_mcp.tools_categories import create_category, set_category_budget

__all__ = [
    "WRITE_TAG",
    "approve_transactions",
    "configure",
    "create_category",
    "create_transactions",
    "find_transactions",
    "get_budget_vs_actual",
    "get_category_balances",
    "get_monthly_summary",
    "get_spending_trends",
    "list_accounts",
    "list_plans",
    "list_scheduled_transactions",
    "list_category_groups",
    "http_options",
    "main",
    "mcp",
    "set_category_budget",
    "today",
]

logger = logging.getLogger(__name__)


def http_options(token: SecretStr | None) -> dict[str, Any]:
    """Say what guards the HTTP transport, besides listening on 127.0.0.1.

    The Host and Origin headers must name this machine, so a web page cannot reach
    the server through DNS rebinding; with a token, every request must carry it.

    Args:
        token: AVENIR_MCP_HTTP_TOKEN, or None.

    Returns:
        Keyword arguments for FastMCP's run().
    """
    return {"host_origin_protection": True, "middleware": http_auth.middleware(token)}


def main(argv: list[str] | None = None) -> None:
    """Run the server: stdio by default, streamable HTTP when AVENIR_MCP_TRANSPORT=http.

    `avenir-mcp --version` prints the version and exits, for bug reports. The server
    takes no other argument: its configuration is in the environment.

    Read-only unless AVENIR_MCP_WRITE=1: write tools are then registered too.
    Diagnostics go to stderr (stdout belongs to the protocol in stdio mode), at
    AVENIR_MCP_LOG_LEVEL, WARNING by default, as text or, with
    AVENIR_MCP_LOG_FORMAT=json, one JSON object per line.

    The HTTP address comes from AVENIR_MCP_HOST and AVENIR_MCP_PORT and defaults to
    127.0.0.1:8103, so the server is never reachable from the network by accident.
    Over HTTP, requests must name this machine (see http_options); writes also need
    AVENIR_MCP_HTTP_TOKEN, which every request must then carry.

    Args:
        argv: The command-line arguments; None for sys.argv.

    Raises:
        SystemExit: If writes are enabled over HTTP without AVENIR_MCP_HTTP_TOKEN.
    """
    if (sys.argv[1:] if argv is None else argv) == ["--version"]:
        print(f"avenir-mcp {__version__}")
        return
    logs.configure(
        os.getenv("AVENIR_MCP_LOG_LEVEL", "WARNING").upper(),
        os.getenv("AVENIR_MCP_LOG_FORMAT", "text"),
    )
    writes = os.getenv("AVENIR_MCP_WRITE") == "1"
    configure(enable_writes=writes)
    if os.getenv("AVENIR_MCP_TRANSPORT", "stdio") == "http":
        host = os.getenv("AVENIR_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("AVENIR_MCP_PORT", "8103"))
        configured = os.getenv("AVENIR_MCP_HTTP_TOKEN")
        # Masked from here on: a repr of the options, logged or printed, shows no token.
        token = SecretStr(configured) if configured else None
        if writes and token is None:
            sys.exit(
                "AVENIR_MCP_WRITE=1 over HTTP needs AVENIR_MCP_HTTP_TOKEN: set it to a long "
                "random value and send it as Authorization: Bearer <token>."
            )
        logger.info("Starting avenir-mcp on %s:%d", host, port)
        mcp.run(transport="streamable-http", host=host, port=port, **http_options(token))
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
