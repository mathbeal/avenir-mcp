"""Entry point of the Avenir MCP server.

Importing the tool modules registers their tools on the shared server instance.
"""

from __future__ import annotations

import logging
import os

from avenir_mcp import (  # noqa: F401  pylint: disable=unused-import
    tools_accounts,
    tools_categories,
    tools_classify,
    tools_undo,
)
from avenir_mcp.app import WRITE_TAG, configure, mcp, today
from avenir_mcp.tools_budget import (
    approve_transactions,
    create_category,
    create_transactions,
    get_budget_vs_actual,
    get_category_balances,
    get_monthly_summary,
    get_spending_trends,
    list_accounts,
    list_budgets,
    list_category_groups,
)
from avenir_mcp.tools_categories import set_category_budget

__all__ = [
    "WRITE_TAG",
    "approve_transactions",
    "configure",
    "create_category",
    "create_transactions",
    "get_budget_vs_actual",
    "get_category_balances",
    "get_monthly_summary",
    "get_spending_trends",
    "list_accounts",
    "list_budgets",
    "list_category_groups",
    "main",
    "mcp",
    "set_category_budget",
    "today",
]

# Diagnostics go to stderr; in stdio mode stdout belongs to the protocol.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the server: stdio by default, streamable HTTP when AVENIR_MCP_TRANSPORT=http.

    Read-only unless AVENIR_MCP_WRITE=1: write tools are then registered too.

    The HTTP address comes from AVENIR_MCP_HOST and AVENIR_MCP_PORT and defaults to
    127.0.0.1:8103, so the server is never reachable from the network by accident.
    """
    configure(enable_writes=os.getenv("AVENIR_MCP_WRITE") == "1")
    if os.getenv("AVENIR_MCP_TRANSPORT", "stdio") == "http":
        host = os.getenv("AVENIR_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("AVENIR_MCP_PORT", "8103"))
        logger.info("Starting avenir-mcp on %s:%d", host, port)
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
