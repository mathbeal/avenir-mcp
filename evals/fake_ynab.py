# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

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

    def __init__(self, language: str = "") -> None:
        """Start from the demo budget as it is on every run, named in one language.

        Args:
            language: A documentation language, or "" for English.
        """
        self.language = language
        self.transactions = {tx["id"]: tx for tx in demo.transactions(language)}
        self.knowledge = 1
        self.changed_at = {tx_id: 1 for tx_id in self.transactions}
        self.budgeted: dict[tuple[str, str], int] = {}
        # Targets set during the run, by category: the demo plan starts with none.
        self.goals: dict[str, dict[str, Any]] = {}
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
                "name": demo.named(name, self.language),
                "category_group_id": demo.group_id(group),
                "category_group_name": demo.named(group, self.language),
                "hidden": False,
                "deleted": False,
                **self.goals.get(cat_id, {}),
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
            (demo.CHECKING, demo.named("Checking", self.language), "checking"),
            (demo.SAVINGS, demo.named("Savings", self.language), "savings"),
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
                    # The checking account is imported from the bank; savings is kept by hand.
                    "direct_import_linked": acc_id == demo.CHECKING,
                    "direct_import_in_error": False,
                    "last_reconciled_at": (
                        "2026-08-31T18:02:11.000Z" if acc_id == demo.CHECKING else None
                    ),
                }
            )
        return result

    # --- writes ----------------------------------------------------------

    def touch(self, tx_id: str) -> None:
        """Record a change for delta sync."""
        self.knowledge += 1
        self.changed_at[tx_id] = self.knowledge

    def patch_transactions(self, updates: list[dict[str, Any]]) -> list[str]:
        """Apply category, cleared, approved or split changes."""
        names = {c["id"]: c["name"] for c in self.categories()}
        for update in updates:
            tx = self.transactions[update["id"]]
            for key in ("category_id", "cleared", "approved", "flag_color"):
                if key in update:
                    tx[key] = update[key]
            if "subtransactions" in update:
                tx["subtransactions"] = [
                    {"id": f"{tx['id']}-{i}", "deleted": False, **sub}
                    for i, sub in enumerate(update["subtransactions"])
                ]
            tx["category_name"] = names.get(tx["category_id"] or "")
            self.touch(tx["id"])
        return [u["id"] for u in updates]

    def set_goal(self, cat_id: str, fields: dict[str, Any]) -> None:
        """Set a category's target as YNAB does: a date or a frequency, or none at all."""
        if fields.get("goal_target") is None:
            self.goals.pop(cat_id, None)
            return
        goal = {"goal_type": "NEED", "goal_target": fields["goal_target"]}
        cadences = {"monthly": 1, "weekly": 2, "yearly": 13}
        if "goal_target_date" in fields:
            goal |= {"goal_target_date": fields["goal_target_date"], "goal_cadence": 0}
        else:
            goal |= {"goal_cadence": cadences[fields.get("goal_frequency", "monthly")]}
        self.goals[cat_id] = goal | {"goal_cadence_frequency": 1}

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
                "account_name": demo.named(
                    "Checking" if item["account_id"] == demo.CHECKING else "Savings", self.language
                ),
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
            if (method, path) == ("GET", "/plans"):
                budget = {
                    "id": demo.PLAN_ID,
                    "name": demo.named("Demo household", STATE.language),
                    "last_modified_on": "2026-09-20",
                    "first_month": demo.MONTHS[0],
                    "last_month": demo.MONTHS[-1],
                }
                return self._send(200, {"data": {"plans": [budget]}})
            # YNAB accepts "last-used" wherever a budget id goes.
            match = re.match(rf"^/plans/(?:{demo.PLAN_ID}|last-used)(/.*)$", path)
            if not match:
                return self._send(404, {"error": {"detail": "Resource not found"}})
            rest = match.group(1)
            if method == "GET" and rest == "/accounts":
                return self._send(200, {"data": {"accounts": STATE.accounts()}})
            if method == "GET" and rest == "/categories":
                groups = [
                    {
                        "id": demo.group_id(name),
                        "name": demo.named(name, STATE.language),
                        "hidden": False,
                        "deleted": False,
                        "categories": [
                            c
                            for c in STATE.categories()
                            if c["category_group_id"] == demo.group_id(name)
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
            if method == "GET" and rest == "/scheduled_transactions":
                data = {
                    "scheduled_transactions": demo.scheduled(STATE.language),
                    "server_knowledge": 1,
                }
                return self._send(200, {"data": data})
            if method == "PATCH" and rest == "/transactions":
                ids = STATE.patch_transactions(self._body()["transactions"])
                return self._send(200, {"data": {"transaction_ids": ids}})
            if method == "POST" and rest == "/transactions/import":
                # The demo plan has no bank connection: there is never anything new.
                return self._send(200, {"data": {"transaction_ids": []}})
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
            if method == "PATCH" and (cat := self._patch_category(rest)):
                return self._send(200, {"data": {"category": cat}})
            return self._send(404, {"error": {"detail": f"Not in the demo: {method} {path}"}})

    def _patch_category(self, rest: str) -> dict[str, Any] | None:
        """A month's budgeted amount, or a category's target; None for any other path."""
        if budget_match := re.match(r"^/months/([^/]+)/categories/([^/]+)$", rest):
            month, cat_id = budget_match.groups()
            STATE.budgeted[(month, cat_id)] = self._body()["category"]["budgeted"]
            cats: list[dict[str, Any]] = STATE.month(month)["categories"]
            return next(c for c in cats if c["id"] == cat_id)
        if target_match := re.match(r"^/categories/([^/]+)$", rest):
            cat_id = target_match.group(1)
            STATE.set_goal(cat_id, self._body()["category"])
            return next(c for c in STATE.categories() if c["id"] == cat_id)
        return None

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
