"""Capture real tool answers on the demo budget, for the documentation.

Every example in the docs is what Avenir actually returns on the invented demo
budget, with the date fixed and random identifiers replaced by placeholders, so
the files only change when the behaviour does.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastmcp import Client

from evals import fake_ynab

TODAY = date(2026, 9, 25)
BUDGET = "demo-budget"


def _placeholders(data: Any) -> Any:
    """Replace random confirmation codes and operation ids."""
    if isinstance(data, dict):
        out = {}
        for key, value in data.items():
            if key == "confirmation" and value:
                out[key] = "<confirmation code>"
            elif key == "operation_id" and value:
                out[key] = "<operation id>"
            else:
                out[key] = _placeholders(value)
        return out
    if isinstance(data, list):
        return [_placeholders(item) for item in data]
    if isinstance(data, str) and "operation_id " in data:
        head, _, tail = data.partition("operation_id ")
        return head + "operation_id <operation id>" + tail[tail.find(" ") :]
    return data


def _trim(data: Any, items: int = 4) -> Any:
    """Keep the first few entries of long lists, saying how many were left out."""
    if isinstance(data, list) and len(data) > items:
        return [_trim(d, items) for d in data[:items]] + [f"… {len(data) - items} more"]
    if isinstance(data, dict):
        return {k: _trim(v, items) for k, v in data.items()}
    return data


# (snippet name, tool, arguments, how many list entries to keep)
CALLS: list[tuple[str, str, dict[str, Any], int]] = [
    ("list_budgets", "list_budgets", {}, 4),
    ("list_accounts", "list_accounts", {"budget_id": BUDGET}, 4),
    ("monthly_summary", "get_monthly_summary", {"budget_id": BUDGET, "month": "2026-09-01"}, 4),
    ("category_balances", "get_category_balances", {"budget_id": BUDGET, "month": "2026-09-01"}, 4),
    ("suggest_categories", "suggest_categories", {"budget_id": BUDGET, "limit": 3}, 3),
    (
        "apply_preview",
        "apply_categories",
        {
            "budget_id": BUDGET,
            "assignments": [
                {"transaction_id": "tx-048", "category_id": "cat-groceries"},
                {"transaction_id": "tx-049", "category_id": "cat-transport"},
            ],
        },
        4,
    ),
    (
        "reconcile_gap",
        "reconcile_account",
        {"budget_id": BUDGET, "account_id": "acc-checking", "bank_balance": 3440.80},
        4,
    ),
    (
        "forecast",
        "forecast_balance",
        {"budget_id": BUDGET, "until": "2026-12", "monthly_income": 3200},
        6,
    ),
    (
        "budget_preview",
        "set_category_budget",
        {
            "budget_id": BUDGET,
            "month": "2026-09-01",
            "category_id": "cat-restaurants",
            "amount": 150,
        },
        4,
    ),
    (
        "create_preview",
        "create_transactions",
        {
            "budget_id": BUDGET,
            "account_id": "acc-checking",
            "transactions": [
                {
                    "date": "2026-09-21",
                    "amount": -32.4,
                    "payee_name": "Pharmacie Centrale",
                    "memo": "not imported by the bank",
                }
            ],
        },
        4,
    ),
    ("bad_month", "get_monthly_summary", {"budget_id": BUDGET, "month": "2026-13-01"}, 4),
]


async def _capture() -> dict[str, str]:
    from avenir_mcp import server  # pylint: disable=import-outside-toplevel

    snippets: dict[str, str] = {}
    async with Client(server.mcp) as mcp_client:
        for name, tool, args, keep in CALLS:
            result = await mcp_client.call_tool(tool, args, raise_on_error=False)
            if result.is_error:
                snippets[name] = result.content[0].text + "\n"
                continue
            data = result.structured_content
            if isinstance(data, dict) and set(data) == {"result"}:
                data = data["result"]
            text = json.dumps(_trim(_placeholders(data), keep), indent=2, ensure_ascii=False)
            snippets[name] = text + "\n"
    return snippets


def generate() -> dict[str, str]:
    """Run the calls against a fresh demo budget; return snippet name -> text."""
    fake_ynab.STATE = fake_ynab.DemoBudget()
    demo = fake_ynab.serve()
    try:
        with tempfile.TemporaryDirectory() as work:
            env = {
                "YNAB_API_KEY": "demo",
                "AVENIR_MCP_YNAB_URL": f"http://127.0.0.1:{demo.server_port}/v1",
                "AVENIR_MCP_JOURNAL": str(Path(work) / "journal.jsonl"),
            }
            with patch.dict(os.environ, env), patch("avenir_mcp.app.today", lambda: TODAY):
                from avenir_mcp import client  # pylint: disable=import-outside-toplevel

                client._CACHE.clear()  # pylint: disable=protected-access
                return asyncio.run(_capture())
    finally:
        demo.shutdown()
        demo.server_close()
