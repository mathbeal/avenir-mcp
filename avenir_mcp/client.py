"""YNAB API v1 wrapper — async httpx client with in-memory delta-sync cache."""

from __future__ import annotations

import logging
import math
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx  # pylint: disable=import-error
from pydantic import SecretStr  # pylint: disable=import-error

logger = logging.getLogger(__name__)

_YNAB_URL = "https://api.ynab.com/v1"


_THIS_MACHINE = {"127.0.0.1", "localhost", "::1"}


def _base_url() -> str:
    """Give YNAB's API, or AVENIR_MCP_YNAB_URL (a demo budget server for evaluations).

    Every request carries the token, so it goes over https — plain http only to a
    stand-in on this machine.

    Returns:
        The base URL, without a trailing slash.

    Raises:
        RuntimeError: If AVENIR_MCP_YNAB_URL would send the token in clear.
    """
    url = os.getenv("AVENIR_MCP_YNAB_URL", _YNAB_URL).rstrip("/")
    parts = urlsplit(url)
    if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in _THIS_MACHINE):
        raise RuntimeError(
            f"AVENIR_MCP_YNAB_URL must start with https:// (plain http only for "
            f"127.0.0.1 or localhost), got {url!r}."
        )
    return url


# One path segment of a YNAB id, month or resource name: UUIDs, "last-used",
# "2026-09-01". Nothing that could add a segment, climb one, or start a query.
_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def _url(path: str) -> str:
    """Build the full URL of an API path whose every segment is a plain id or name.

    Ids come from agents, and an agent may have read a malicious memo: an id such
    as "x/../../user" must not steer a request to another endpoint.

    Args:
        path: The API path, such as "/budgets/{id}/accounts".

    Returns:
        The base URL followed by the path.

    Raises:
        ValueError: If a segment is not a YNAB id.
    """
    for segment in path.strip("/").split("/"):
        if not _SEGMENT.fullmatch(segment):
            raise ValueError(
                f"{segment!r} is not a YNAB id: use the ids returned by list_budgets, "
                "list_accounts or the other tools."
            )
    return f"{_base_url()}{path}"


# The budget YNAB last opened: a moving target, never cached.
LAST_USED = "last-used"

# Delta-sync cache: {budget_id: {"server_knowledge": int, "transactions": {tx_id: tx}}}
_CACHE: dict[str, dict[str, Any]] = {}


def _api_key() -> SecretStr:
    """Return the YNAB Personal Access Token: YNAB_API_KEY, or the file YNAB_API_KEY_FILE.

    The file keeps the token out of MCP client configurations. Like an SSH key, it
    must be readable by its owner only.

    Returns:
        The token, shown as a mask when printed or logged.

    Raises:
        RuntimeError: If neither is set, or the file is missing or readable by others.
    """
    key = os.getenv("YNAB_API_KEY", "")
    if key:
        return SecretStr(key)
    path = os.getenv("YNAB_API_KEY_FILE", "")
    if not path:
        raise RuntimeError(
            "YNAB_API_KEY environment variable is not set (nor YNAB_API_KEY_FILE, a file "
            "holding the token)"
        )
    try:
        mode = os.stat(path).st_mode
        key = Path(path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(f"YNAB_API_KEY_FILE cannot be read: {error.strerror}") from error
    if os.name == "posix" and mode & 0o077:
        raise RuntimeError(f"YNAB_API_KEY_FILE is readable by other users: run chmod 600 {path}")
    return SecretStr(key)


def milliunit_to_amount(milliunit: int) -> float:
    """Convert a YNAB milliunit integer to a decimal amount.

    YNAB stores all monetary values in milliunits (1 unit = 1000 milliunits).

    Args:
        milliunit: Raw YNAB milliunit value (may be negative for expenses).

    Returns:
        Decimal amount (e.g. 500000 → 500.0, -75000 → -75.0).

    Examples:
        >>> milliunit_to_amount(500000)
        500.0
        >>> milliunit_to_amount(-75000)
        -75.0
        >>> milliunit_to_amount(0)
        0.0
    """
    return milliunit / 1000


def _check(response: Any) -> dict[str, Any]:
    """Check a response: its JSON body, or YNAB's own error detail on a 4xx/5xx.

    Args:
        response: The httpx response.

    Returns:
        The JSON body.

    Raises:
        RuntimeError: "YNAB <status>: <detail>" when the API rejects the request.
    """
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("detail", "")
        except ValueError:
            detail = response.text
        raise RuntimeError(f"YNAB {response.status_code}: {detail}")
    return response.json()  # type: ignore[no-any-return]


# YNAB answers in well under a second; a stuck request should fail, not hang the agent.
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    """Send an authenticated request to a YNAB API path.

    The path is checked before anything is opened: a bad id never reaches the network.

    Args:
        method: get, patch, post or delete.
        path: The API path.
        **kwargs: Passed to httpx: params, json.

    Returns:
        The response's JSON body.

    Raises:
        ValueError: If a path segment is not a YNAB id.
        RuntimeError: On 4xx/5xx responses, with YNAB's error detail.
    """
    url = _url(path)
    headers = {"Authorization": f"Bearer {_api_key().get_secret_value()}"}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        send = getattr(client, method)  # client.get, .patch, .post or .delete
        response = await send(url, headers=headers, **kwargs)
        return _check(response)


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET a YNAB API path, with optional query parameters.

    Args:
        path: The API path.
        params: Query parameters, if any.

    Returns:
        The response's JSON body.
    """
    return await _request("get", path, params=params or {})


async def _patch(path: str, body: dict[str, Any]) -> dict[str, Any]:
    """PATCH a YNAB API path with a JSON body.

    Args:
        path: The API path.
        body: The JSON body.

    Returns:
        The response's JSON body.
    """
    return await _request("patch", path, json=body)


async def _post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST a JSON body to a YNAB API path.

    Args:
        path: The API path.
        body: The JSON body.

    Returns:
        The response's JSON body.
    """
    return await _request("post", path, json=body)


async def _delete(path: str) -> dict[str, Any]:
    """DELETE a YNAB API path.

    Args:
        path: The API path.

    Returns:
        The response's JSON body.
    """
    return await _request("delete", path)


async def get_budgets() -> list[dict[str, Any]]:
    """Return all YNAB budgets accessible with the current API key.

    Returns:
        List of budget dicts with id, name, first_month, last_month.
    """
    logger.info("Fetching budget list")
    data = await _get("/budgets")
    return data["data"]["budgets"]  # type: ignore[no-any-return]


async def get_categories(budget_id: str) -> list[dict[str, Any]]:
    """Return all non-hidden categories for the given budget (flattened).

    Args:
        budget_id: YNAB budget UUID or "last-used".

    Returns:
        Flat list of category dicts (id, name, category_group_id, hidden, …).
    """
    logger.info("Fetching categories for budget %s", budget_id)
    data = await _get(f"/budgets/{budget_id}/categories")
    groups: list[dict[str, Any]] = data["data"]["category_groups"]
    categories: list[dict[str, Any]] = []
    for group in groups:
        for cat in group.get("categories", []):
            if not cat.get("hidden", False):
                categories.append(cat)
    return categories


async def get_month(budget_id: str, month: str = "current") -> dict[str, Any]:
    """Return the summary for a single budget month.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        month: ISO month string "YYYY-MM-01" or the literal "current".

    Returns:
        Month dict with budgeted, activity, balance, income, overspend.
    """
    logger.info("Fetching month %s for budget %s", month, budget_id)
    data = await _get(f"/budgets/{budget_id}/months/{month}")
    return data["data"]["month"]  # type: ignore[no-any-return]


async def get_month_categories(budget_id: str, month: str = "current") -> list[dict[str, Any]]:
    """Return per-category budget/actual data for a given month.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        month: ISO month string "YYYY-MM-01" or "current".

    Returns:
        List of category dicts enriched with budgeted, activity, balance for that month.
    """
    logger.info("Fetching month categories for %s / %s", budget_id, month)
    month_data = await get_month(budget_id, month)
    categories: list[dict[str, Any]] = []
    for group in month_data.get("categories", []):
        if isinstance(group, dict) and "categories" in group:
            categories.extend(group["categories"])
        else:
            categories.append(group)
    return categories


async def get_transactions(
    budget_id: str,
    since_date: str | None = None,
    category_id: str | None = None,
    uncategorized_only: bool = False,
) -> list[dict[str, Any]]:
    """Return transactions for a budget, with optional filters.

    Uses delta sync (last_knowledge_of_server) to minimise API calls when
    called repeatedly for the same budget without filters.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        since_date: ISO date "YYYY-MM-DD"; only return transactions on/after.
        category_id: Filter to a specific category UUID.
        uncategorized_only: If True, only return uncategorized transactions.

    Returns:
        List of transaction dicts.
    """
    if category_id:
        logger.info("Fetching transactions for category %s", category_id)
        data = await _get(f"/budgets/{budget_id}/categories/{category_id}/transactions")
        return data["data"]["transactions"]  # type: ignore[no-any-return]

    params: dict[str, Any] = {}
    if since_date:
        params["since_date"] = since_date
    if uncategorized_only:
        params["type"] = "uncategorized"

    # Delta sync, only for a named budget and no filter: "last-used" may name another
    # budget from one call to the next, and changes are counted per budget.
    cache_key = budget_id
    cached = not since_date and not uncategorized_only and budget_id != LAST_USED
    if cached and cache_key in _CACHE:
        params["last_knowledge_of_server"] = _CACHE[cache_key]["server_knowledge"]
        logger.info(
            "Delta sync: fetching transactions for %s since knowledge=%s",
            budget_id,
            params["last_knowledge_of_server"],
        )
    else:
        logger.info("Fetching transactions for budget %s (full load)", budget_id)

    data = await _get(f"/budgets/{budget_id}/transactions", params=params)
    payload = data["data"]
    transactions: list[dict[str, Any]] = payload["transactions"]
    if not cached:
        return [tx for tx in transactions if not tx.get("deleted")]

    # A delta only holds what changed since the last load: merge it into the
    # cached transactions, dropping the deleted ones.
    known: dict[str, dict[str, Any]] = _CACHE.get(cache_key, {}).get("transactions", {})
    for tx in transactions:
        if tx.get("deleted"):
            known.pop(tx["id"], None)
        else:
            known[tx["id"]] = tx
    _CACHE[cache_key] = {
        "server_knowledge": payload.get("server_knowledge", 0),
        "transactions": known,
    }
    return list(known.values())


async def get_months(budget_id: str) -> list[dict[str, Any]]:
    """Return all available months for a budget, ordered chronologically.

    Args:
        budget_id: YNAB budget UUID or "last-used".

    Returns:
        List of month summary dicts with month, budgeted, activity, balance.
    """
    logger.info("Fetching months list for budget %s", budget_id)
    data = await _get(f"/budgets/{budget_id}/months")
    return data["data"]["months"]  # type: ignore[no-any-return]


# YNAB system groups (Ready to Assign, card payments, hidden bin): no user categories there.
_SYSTEM_GROUPS = {"Internal Master Category", "Credit Card Payments", "Hidden Categories"}


async def get_category_groups(budget_id: str) -> list[dict[str, Any]]:
    """Return the user-visible category groups of a budget (id and name only).

    Hidden, deleted and system groups are skipped: new categories cannot go there.

    Args:
        budget_id: YNAB budget UUID or "last-used".

    Returns:
        List of {"id", "name"} dicts.
    """
    logger.info("Fetching category groups for budget %s", budget_id)
    data = await _get(f"/budgets/{budget_id}/categories")
    return [
        {"id": group["id"], "name": group["name"]}
        for group in data["data"]["category_groups"]
        if not group.get("hidden", False)
        and not group.get("deleted", False)
        and group["name"] not in _SYSTEM_GROUPS
    ]


async def create_category(budget_id: str, category_group_id: str, name: str) -> dict[str, Any]:
    """Create a new category in a budget.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        category_group_id: UUID of the (non-internal) group to create it in.
        name: Name of the new category.

    Returns:
        The created category dict from the YNAB API response.
    """
    logger.info("Creating a category in group %s", category_group_id)
    body = {"category": {"name": name, "category_group_id": category_group_id}}
    data = await _post(f"/budgets/{budget_id}/categories", body)
    return data["data"]["category"]  # type: ignore[no-any-return]


def amount_to_milliunit(amount: float) -> int:
    """Convert a decimal amount to YNAB milliunits, rounding to avoid float drift.

    Args:
        amount: An amount in currency units.

    Returns:
        The amount in milliunits (thousandths of the currency unit).

    Raises:
        ValueError: If the amount is not a finite number.

    Examples:
        >>> amount_to_milliunit(111.32)
        111320
    """
    if not math.isfinite(amount):
        raise ValueError(f"An amount must be a finite number, got {amount!r}.")
    return round(amount * 1000)


async def set_category_budgeted(
    budget_id: str, month: str, category_id: str, amount: float
) -> dict[str, Any]:
    """Set the amount assigned to a category for one month (absolute, not a delta).

    Args:
        budget_id: YNAB budget UUID or "last-used".
        month: ISO month "YYYY-MM-01" or "current".
        category_id: Category UUID.
        amount: Amount to assign, in currency units (e.g. 1890.0).

    Returns:
        The updated month-category dict from the YNAB API response.
    """
    logger.info("Setting the budgeted amount of category %s for %s", category_id, month)
    body = {"category": {"budgeted": amount_to_milliunit(amount)}}
    data = await _patch(f"/budgets/{budget_id}/months/{month}/categories/{category_id}", body)
    return data["data"]["category"]  # type: ignore[no-any-return]


async def get_accounts(budget_id: str) -> list[dict[str, Any]]:
    """Return the non-deleted accounts of a budget, balances in currency units.

    Args:
        budget_id: YNAB budget UUID or "last-used".

    Returns:
        List of dicts: id, name, type, on_budget, closed, balance,
        cleared_balance, uncleared_balance.
    """
    logger.info("Fetching accounts for budget %s", budget_id)
    data = await _get(f"/budgets/{budget_id}/accounts")
    return [
        {
            "id": acc["id"],
            "name": acc["name"],
            "type": acc["type"],
            "on_budget": acc["on_budget"],
            "closed": acc["closed"],
            "balance": milliunit_to_amount(acc["balance"]),
            "cleared_balance": milliunit_to_amount(acc["cleared_balance"]),
            "uncleared_balance": milliunit_to_amount(acc["uncleared_balance"]),
        }
        for acc in data["data"]["accounts"]
        if not acc.get("deleted", False)
    ]


_OPTIONAL_TX_FIELDS = ("memo", "category_id", "import_id")


async def create_transactions(
    budget_id: str, account_id: str, items: list[dict[str, Any]], approved: bool = True
) -> dict[str, Any]:
    """Create cleared transactions on one account, approved unless told otherwise.

    Each item needs date ("YYYY-MM-DD"), amount (currency units, negative for
    outflows) and payee_name; memo, category_id and import_id are optional.
    YNAB skips any item whose import_id already exists on the account.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        account_id: Account UUID the transactions belong to.
        items: Transactions to create.
        approved: False leaves them for the user to review in YNAB.

    Returns:
        {"created", "transaction_ids", "duplicate_import_ids"}.
    """
    transactions = []
    for item in items:
        tx: dict[str, Any] = {
            "account_id": account_id,
            "date": item["date"],
            "amount": amount_to_milliunit(item["amount"]),
            "payee_name": item["payee_name"],
        }
        tx.update({key: item[key] for key in _OPTIONAL_TX_FIELDS if item.get(key)})
        tx.update({"cleared": "cleared", "approved": approved})
        transactions.append(tx)
    logger.info("Creating %d transactions on account %s", len(transactions), account_id)
    data = await _post(f"/budgets/{budget_id}/transactions", {"transactions": transactions})
    payload = data["data"]
    return {
        "created": len(payload.get("transaction_ids", [])),
        "transaction_ids": payload.get("transaction_ids", []),
        "duplicate_import_ids": payload.get("duplicate_import_ids", []),
    }


async def approve_transactions(budget_id: str, tx_ids: list[str]) -> dict[str, int]:
    """Mark transactions as approved (reviewed) in one bulk request.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        tx_ids: Transaction UUIDs to approve.

    Returns:
        {"approved": number of transactions YNAB updated}.
    """
    if not tx_ids:
        return {"approved": 0}
    logger.info("Approving %d transactions", len(tx_ids))
    body = {"transactions": [{"id": tx_id, "approved": True} for tx_id in tx_ids]}
    data = await _patch(f"/budgets/{budget_id}/transactions", body)
    return {"approved": len(data["data"].get("transaction_ids", []))}


async def set_transaction_categories(
    budget_id: str, moves: list[tuple[str, str | None]]
) -> list[str]:
    """Give each transaction a category in one bulk request.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        moves: (transaction_id, category_id) pairs; None clears the category.

    Returns:
        The ids of the transactions YNAB updated.
    """
    if not moves:
        return []
    logger.info("Setting the category of %d transactions", len(moves))
    body = {"transactions": [{"id": tx_id, "category_id": cat} for tx_id, cat in moves]}
    data = await _patch(f"/budgets/{budget_id}/transactions", body)
    return list(data["data"].get("transaction_ids", []))


async def update_category(
    budget_id: str,
    category_id: str,
    name: str | None = None,
    category_group_id: str | None = None,
) -> dict[str, Any]:
    """Rename a category and/or move it to another group.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        category_id: Category to update.
        name: New name, or None to keep it.
        category_group_id: Group to move it to, or None to keep it.

    Returns:
        The updated category dict.
    """
    fields: dict[str, str] = {}
    if name is not None:
        fields["name"] = name
    if category_group_id is not None:
        fields["category_group_id"] = category_group_id
    logger.info("Updating category %s (%s)", category_id, ", ".join(fields))
    data = await _patch(f"/budgets/{budget_id}/categories/{category_id}", {"category": fields})
    return data["data"]["category"]  # type: ignore[no-any-return]


async def set_transactions_cleared(budget_id: str, tx_ids: list[str], cleared: str) -> list[str]:
    """Set the cleared status of transactions in one bulk request.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        tx_ids: Transaction UUIDs to update.
        cleared: "cleared", "uncleared" or "reconciled".

    Returns:
        The ids of the transactions YNAB updated.
    """
    if not tx_ids:
        return []
    logger.info("Marking %d transactions %s", len(tx_ids), cleared)
    body = {"transactions": [{"id": tx_id, "cleared": cleared} for tx_id in tx_ids]}
    data = await _patch(f"/budgets/{budget_id}/transactions", body)
    return list(data["data"].get("transaction_ids", []))


async def delete_transaction(budget_id: str, tx_id: str) -> None:
    """Delete one transaction.

    Args:
        budget_id: YNAB budget UUID or "last-used".
        tx_id: Transaction UUID.
    """
    logger.info("Deleting transaction %s", tx_id)
    await _delete(f"/budgets/{budget_id}/transactions/{tx_id}")
