"""A local stand-in for YNAB's API, serving the demo budget.

Only what avenir-mcp calls is implemented, with YNAB's response shapes. State lives
in memory so an evaluation can check what an agent changed.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from evals import demo_budget as demo


class DemoBudget:  # pylint: disable=too-many-instance-attributes
    """The demo budget's mutable state."""

    def __init__(self) -> None:
        self.transactions = {tx["id"]: tx for tx in demo.transactions()}
        self.knowledge = 1
        self.changed_at = {tx_id: 1 for tx_id in self.transactions}
        self.budgeted: dict[tuple[str, str], int] = {}
        self.groups = {name: [list(c) for c in cats] for name, cats in demo.GROUPS.items()}
        self.lock = threading.Lock()
        self.next_id = len(self.transactions)
        # Requests served, so the documentation can state what each tool costs.
        self.requests = 0

    # --- reads -----------------------------------------------------------

    def categories(self) -> list[dict[str, Any]]:
        """Flat category list with group names."""
        return [
            {
                "id": cat_id,
                "name": name,
                "category_group_id": f"grp-{group.lower().replace(' ', '-')}",
                "category_group_name": group,
                "hidden": False,
                "deleted": False,
            }
            for group, cats in self.groups.items()
            for cat_id, name in cats
        ]

    def month(self, month: str) -> dict[str, Any]:
        """A month with its categories, computed from the transactions."""
        live = [
            tx
            for tx in self.transactions.values()
            if not tx["deleted"] and tx["date"][:7] == month[:7]
        ]
        cats = []
        for cat in self.categories():
            budgeted = self.budgeted.get((month, cat["id"]), demo.BUDGETED.get(cat["id"], 0))
            activity = sum(tx["amount"] for tx in live if tx["category_id"] == cat["id"])
            if cat["id"] == "cat-inflow":
                budgeted, activity = 0, 0
            cats.append(
                {**cat, "budgeted": budgeted, "activity": activity, "balance": budgeted + activity}
            )
        income = sum(tx["amount"] for tx in live if tx["category_id"] == "cat-inflow")
        budgeted_total = sum(c["budgeted"] for c in cats)
        # Ready to Assign carries over: all income so far minus all money budgeted so far.
        earned = sum(
            tx["amount"]
            for tx in self.transactions.values()
            if not tx["deleted"]
            and tx["category_id"] == "cat-inflow"
            and tx["date"][:7] <= month[:7]
        )
        assigned = sum(
            self.budgeted.get((m, cat_id), demo.BUDGETED.get(cat_id, 0))
            for m in demo.MONTHS
            if m <= month
            for cat_id in demo.BUDGETED
        )
        return {
            "month": month,
            "income": income,
            "budgeted": budgeted_total,
            "activity": sum(c["activity"] for c in cats),
            "to_be_budgeted": earned - assigned,
            "age_of_money": 18,
            "note": None,
            "deleted": False,
            "categories": cats,
        }

    def accounts(self) -> list[dict[str, Any]]:
        """The two demo accounts with balances from their transactions."""
        result = []
        for acc_id, name, kind in (
            (demo.CHECKING, "Checking", "checking"),
            (demo.SAVINGS, "Savings", "savings"),
        ):
            txs = [
                t
                for t in self.transactions.values()
                if t["account_id"] == acc_id and not t["deleted"]
            ]
            cleared = sum(t["amount"] for t in txs if t["cleared"] != "uncleared")
            total = sum(t["amount"] for t in txs)
            result.append(
                {
                    "id": acc_id,
                    "name": name,
                    "type": kind,
                    "on_budget": True,
                    "closed": False,
                    "deleted": False,
                    "balance": total,
                    "cleared_balance": cleared,
                    "uncleared_balance": total - cleared,
                }
            )
        return result

    # --- writes ----------------------------------------------------------

    def touch(self, tx_id: str) -> None:
        """Record a change for delta sync."""
        self.knowledge += 1
        self.changed_at[tx_id] = self.knowledge

    def patch_transactions(self, updates: list[dict[str, Any]]) -> list[str]:
        """Apply category, cleared or approved changes."""
        names = {c["id"]: c["name"] for c in self.categories()}
        for update in updates:
            tx = self.transactions[update["id"]]
            for key in ("category_id", "cleared", "approved"):
                if key in update:
                    tx[key] = update[key]
            tx["category_name"] = names.get(tx["category_id"] or "")
            self.touch(tx["id"])
        return [u["id"] for u in updates]

    def create_transactions(self, items: list[dict[str, Any]]) -> list[str]:
        """Add transactions."""
        ids = []
        for item in items:
            tx_id = f"tx-{self.next_id:03d}"
            self.next_id += 1
            self.transactions[tx_id] = {
                "id": tx_id,
                "memo": None,
                "category_id": None,
                "transfer_account_id": None,
                "deleted": False,
                "account_name": "Checking" if item["account_id"] == demo.CHECKING else "Savings",
                **item,
            }
            self.touch(tx_id)
            ids.append(tx_id)
        return ids


STATE = DemoBudget()


class Handler(BaseHTTPRequestHandler):
    """Routes YNAB API paths to the demo budget."""

    # The standard library names this parameter `format`.
    def log_message(self, format: str, *args: Any) -> None:  # pylint: disable=redefined-builtin
        """Stay silent: the evaluation reports what matters."""

    def _send(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    # One route per YNAB endpoint avenir-mcp calls: a flat dispatch reads best here.
    # pylint: disable-next=too-many-return-statements,too-many-branches,too-many-locals
    def _route(self, method: str) -> None:
        url = urlparse(self.path)
        path = re.sub(r"^/v1", "", url.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        with STATE.lock:
            STATE.requests += 1
            if (method, path) == ("GET", "/budgets"):
                budget = {
                    "id": demo.BUDGET_ID,
                    "name": "Demo household",
                    "last_modified_on": "2026-09-20",
                    "first_month": demo.MONTHS[0],
                    "last_month": demo.MONTHS[-1],
                }
                return self._send(200, {"data": {"budgets": [budget]}})
            # YNAB accepts "last-used" wherever a budget id goes.
            match = re.match(rf"^/budgets/(?:{demo.BUDGET_ID}|last-used)(/.*)$", path)
            if not match:
                return self._send(404, {"error": {"detail": "Resource not found"}})
            rest = match.group(1)
            if method == "GET" and rest == "/accounts":
                return self._send(200, {"data": {"accounts": STATE.accounts()}})
            if method == "GET" and rest == "/categories":
                groups = [
                    {
                        "id": f"grp-{name.lower().replace(' ', '-')}",
                        "name": name,
                        "hidden": False,
                        "deleted": False,
                        "categories": [
                            c for c in STATE.categories() if c["category_group_name"] == name
                        ],
                    }
                    for name in STATE.groups
                ]
                return self._send(200, {"data": {"category_groups": groups}})
            if method == "GET" and rest == "/months":
                months = [{"month": m} for m in demo.MONTHS]
                return self._send(200, {"data": {"months": months}})
            month_match = re.match(r"^/months/([^/]+)$", rest)
            if method == "GET" and month_match:
                month = month_match.group(1)
                month = f"{date.today():%Y-%m}-01" if month == "current" else month
                if month not in demo.MONTHS:
                    return self._send(404, {"error": {"detail": "Resource not found"}})
                return self._send(200, {"data": {"month": STATE.month(month)}})
            if method == "GET" and rest == "/transactions":
                since = int(query.get("last_knowledge_of_server", 0))
                txs = [
                    tx for tx in STATE.transactions.values() if STATE.changed_at[tx["id"]] > since
                ]
                if not since:
                    txs = [tx for tx in txs if not tx["deleted"]]
                if query.get("type") == "uncategorized":
                    txs = [
                        tx for tx in txs if not tx["category_id"] and not tx["transfer_account_id"]
                    ]
                data = {"transactions": txs, "server_knowledge": STATE.knowledge}
                return self._send(200, {"data": data})
            if method == "PATCH" and rest == "/transactions":
                ids = STATE.patch_transactions(self._body()["transactions"])
                return self._send(200, {"data": {"transaction_ids": ids}})
            if method == "POST" and rest == "/transactions":
                ids = STATE.create_transactions(self._body()["transactions"])
                data = {"transaction_ids": ids, "duplicate_import_ids": []}
                return self._send(201, {"data": data})
            delete_match = re.match(r"^/transactions/([^/]+)$", rest)
            if method == "DELETE" and delete_match:
                tx = STATE.transactions[delete_match.group(1)]
                tx["deleted"] = True
                STATE.touch(tx["id"])
                return self._send(200, {"data": {"transaction": tx}})
            budget_match = re.match(r"^/months/([^/]+)/categories/([^/]+)$", rest)
            if method == "PATCH" and budget_match:
                month, cat_id = budget_match.groups()
                STATE.budgeted[(month, cat_id)] = self._body()["category"]["budgeted"]
                cat = next(c for c in STATE.month(month)["categories"] if c["id"] == cat_id)
                return self._send(200, {"data": {"category": cat}})
            return self._send(404, {"error": {"detail": f"Not in the demo: {method} {path}"}})

    def do_GET(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """GET."""
        self._route("GET")

    def do_PATCH(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """PATCH."""
        self._route("PATCH")

    def do_POST(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """POST."""
        self._route("POST")

    def do_DELETE(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """DELETE."""
        self._route("DELETE")


def serve(port: int = 0) -> ThreadingHTTPServer:
    """Start the demo server on 127.0.0.1 in a background thread."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
