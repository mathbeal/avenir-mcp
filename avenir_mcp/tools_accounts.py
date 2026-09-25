"""Account-level tools: reconcile with the bank, forecast the balance."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Literal, TypedDict

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error
from mcp.types import InputRequiredResult  # pylint: disable=import-error

from avenir_mcp import app, client, forecast, journal, reconcile
from avenir_mcp.app import WRITE_TAG, mcp
from avenir_mcp.confirm import WriteStatus, gate

logger = logging.getLogger(__name__)


ReconcileStatus = Literal[
    "applied", "confirmation_required", "declined", "nothing_to_do", "difference_found"
]


class ReconcileResult(TypedDict):
    """The outcome of reconcile_account."""

    status: ReconcileStatus
    message: str
    account: str
    analysis: reconcile.Analysis
    adjustment: float | None
    confirmation: str | None
    operation_id: str | None


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Reconcile an account with the bank",
        "read_only_hint": False,
        "destructive_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
    },
)
async def reconcile_account(  # pylint: disable=too-many-arguments,too-many-locals
    budget_id: str,
    account_id: str,
    bank_balance: float,
    ctx: Context,
    *,
    adjust: bool = False,
    confirmation: str | None = None,
) -> ReconcileResult | InputRequiredResult:
    """Compare an account with the balance your bank shows, then reconcile it.

    Give the balance shown by the bank today (currency units). If YNAB's cleared
    balance differs, nothing is written: the result explains the gap with the
    pending transactions, the one whose amount matches the difference
    (`explained_by`) and likely duplicates. Fix those first (with the user), then
    call again. Only if the user wants to accept the remaining gap, call with
    adjust=true: a "Balance adjustment" transaction is added to Ready to Assign.
    When balances match, every cleared transaction is marked reconciled after the
    user confirms (as for apply_categories). undo_operation reverts it.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        account_id: Account to reconcile (from list_accounts).
        bank_balance: Balance shown by the bank, in currency units.
        adjust: Record the remaining difference as an adjustment.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: reconcile_account(adjust=%s)", adjust)
    accounts = {a["id"]: a["name"] for a in await client.get_accounts(budget_id)}
    if account_id not in accounts:
        raise ToolError(
            f"Account {account_id} is not in this budget: use an id from list_accounts."
        )
    transactions = await client.get_transactions(budget_id)
    analysis = reconcile.analyse(account_id, transactions, bank_balance)
    difference = analysis["difference"]
    result: ReconcileResult = {
        "status": "nothing_to_do",
        "message": "Already reconciled: nothing to do.",
        "account": accounts[account_id],
        "analysis": analysis,
        "adjustment": None,
        "confirmation": None,
        "operation_id": None,
    }
    if difference and not adjust:
        return {
            **result,
            "status": "difference_found",
            "message": (
                f"YNAB's cleared balance differs from the bank by {difference:.2f}. Nothing was "
                "changed. Check explained_by, uncleared and possible_duplicates with the user; "
                "call again once fixed, or with adjust=true to record the gap as an adjustment."
            ),
        }
    if not difference and not analysis["to_reconcile_count"]:
        return result
    question = (
        f"Reconcile {accounts[account_id]}: mark {analysis['to_reconcile_count']} "
        "cleared transaction(s) reconciled"
        + (f" and add a balance adjustment of {difference:.2f}?" if difference else "?")
    )
    subject = {"account": account_id, "balance": bank_balance, "adjust": difference}
    stop = await gate(ctx, budget_id, subject, question, confirmation)
    if stop is not None:
        return stop if isinstance(stop, InputRequiredResult) else {**result, **stop}
    adjustment_id = None
    if difference:
        inflow = next(
            (
                c["id"]
                for c in await client.get_categories(budget_id)
                if c["name"].startswith("Inflow")
            ),
            None,
        )
        created = await client.create_transactions(
            budget_id,
            account_id,
            [
                {
                    "date": date.today().isoformat(),
                    "amount": difference,
                    "payee_name": "Balance adjustment",
                    "memo": "Entered by reconcile_account",
                    "category_id": inflow,
                }
            ],
        )
        adjustment_id = created["transaction_ids"][0]
    to_reconcile = [
        tx["id"]
        for tx in await client.get_transactions(budget_id)
        if tx.get("account_id") == account_id
        and not tx.get("deleted")
        and tx.get("cleared") == "cleared"
    ]
    await client.set_transactions_cleared(budget_id, to_reconcile, "reconciled")
    operation_id = journal.Journal(journal.default_path()).record(
        budget_id,
        "reconcile",
        [],
        {"account_id": account_id, "reconciled_ids": to_reconcile, "adjustment_id": adjustment_id},
    )
    return {
        **result,
        "status": "applied",
        "message": f"Reconciled. undo_operation with operation_id {operation_id} reverts it.",
        "adjustment": difference or None,
        "operation_id": operation_id,
    }


MAX_FORECAST_MONTHS = 24


class ForecastAssumptions(TypedDict):
    """What the projection assumed, so the user can correct it."""

    recurring: list[forecast.Recurring]
    variable_monthly: float
    monthly_income: float
    one_offs: list[forecast.OneOff]


class ForecastResult(TypedDict):
    """A balance projection and what it rests on."""

    message: str
    accounts: list[str]
    start_balance: float
    assumptions: ForecastAssumptions
    months: list[forecast.MonthProjection]
    first_shortfall: str | None


def _check_horizon(until: str, now: date) -> None:
    try:
        year, month = (int(part) for part in until.split("-"))
        date(year, month, 1)
    except ValueError as error:
        raise ToolError(f"until must be a month as YYYY-MM, got {until!r}.") from error
    ahead = (year - now.year) * 12 + month - now.month
    if ahead < 0:
        raise ToolError("until must be the current month or later.")
    if ahead > MAX_FORECAST_MONTHS:
        raise ToolError(f"until must be at most {MAX_FORECAST_MONTHS} months ahead.")


@mcp.tool(
    annotations={
        "title": "Forecast the balance",
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": True,
    }
)
async def forecast_balance(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    budget_id: str,
    until: str,
    account_ids: list[str] | None = None,
    monthly_income: float | None = None,
    variable_monthly: float | None = None,
    one_offs: list[forecast.OneOff] | None = None,
) -> ForecastResult:
    """Project the balance month by month and say when money would run out.

    Starts from today's balance of the open on-budget accounts (or those given).
    For the current month, what was already spent or received since the 1st is
    deducted from the monthly averages, so only what is left is projected.
    Assumes, and returns as `assumptions` so the user can correct them:
    charges that recur in the last 4 months (same payee, stable amount), the
    average of all other spending over the last 3 months, and what you pass:
    expected monthly income (default: the last 3 months' non-recurring inflows,
    which may include one-off money such as capital injections) and one-off amounts
    such as a tax bill (negative) or a refund (positive). Amounts in currency
    units. `lowest` is the lowest point within a month; `first_shortfall` is the
    first month it goes below zero. Changes nothing.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        until: Last month to project, YYYY-MM, at most 24 months ahead.
        account_ids: Accounts to include (from list_accounts); default all open
            on-budget accounts.
        monthly_income: Income expected each month, replacing the income found in
            the history (recurring or average); default: what the history shows.
        variable_monthly: Monthly spending besides recurring charges (negative);
            default: the last 3 months' average.
        one_offs: Expected one-off amounts: {date YYYY-MM-DD, amount, label}.
    """
    logger.info("Tool called: forecast_balance")
    now = app.today()
    _check_horizon(until, now)
    accounts = await client.get_accounts(budget_id)
    if account_ids is not None:
        unknown = sorted(set(account_ids) - {a["id"] for a in accounts})
        if unknown:
            raise ToolError(f"Unknown account(s) {', '.join(unknown)}: use ids from list_accounts.")
        chosen = [a for a in accounts if a["id"] in account_ids]
    else:
        chosen = [a for a in accounts if a["on_budget"] and not a["closed"]]
    ids = {a["id"] for a in chosen}
    history = [tx for tx in await client.get_transactions(budget_id) if tx.get("account_id") in ids]
    charges = forecast.recurring(history, now)
    if monthly_income is not None:
        # The income given replaces what the history suggests, recurring salary included.
        charges = [r for r in charges if r["amount"] < 0]
    variable = (
        variable_monthly
        if variable_monthly is not None
        else forecast.variable_average(history, now, charges)
    )
    income = (
        monthly_income
        if monthly_income is not None
        else forecast.income_average(history, now, charges)
    )
    start = client.milliunit_to_amount(
        sum(client.amount_to_milliunit(a["balance"]) for a in chosen)
    )
    spent, received = forecast.month_to_date(history, now, charges)
    projection = forecast.project(
        start_balance=start,
        today=now,
        until=until,
        recurring=charges,
        variable_monthly=variable,
        monthly_income=income,
        one_offs=one_offs or [],
        spent_this_month=spent,
        received_this_month=received,
    )
    shortfall = projection["first_shortfall"]
    message = (
        f"The balance goes below zero in {shortfall}."
        if shortfall
        else f"The balance stays above zero until {until}."
    ) + " This rests on the assumptions listed: check them with the user."
    return {
        "message": message,
        "accounts": [a["name"] for a in chosen],
        "start_balance": start,
        "assumptions": {
            "recurring": charges,
            "variable_monthly": variable,
            "monthly_income": income,
            "one_offs": one_offs or [],
        },
        "months": projection["months"],
        "first_shortfall": shortfall,
    }


class NewTransaction(TypedDict, total=False):
    """A transaction to create; memo and category_id are optional."""

    date: str
    amount: float
    payee_name: str
    memo: str
    category_id: str


class NewTransactionPreview(TypedDict):
    """A transaction to create, as the user sees it."""

    date: str
    amount: float
    payee: str
    category: str | None
    memo: str | None


class CreateResult(TypedDict):
    """The outcome of create_transactions."""

    status: WriteStatus
    message: str
    account: str
    transactions: list[NewTransactionPreview]
    created_ids: list[str]
    duplicate_import_ids: list[str]
    confirmation: str | None
    operation_id: str | None


def _check_new(items: list[NewTransaction], categories: dict[str, str], now: date) -> None:
    """Refuse what YNAB would refuse, or what cannot be what the user meant."""
    if not items:
        raise ToolError("Give at least one transaction to create.")
    for item in items:
        try:
            when = date.fromisoformat(item["date"])
        except ValueError as error:
            raise ToolError(f"date must be YYYY-MM-DD, got {item['date']!r}.") from error
        if when > now:
            raise ToolError(
                f"{item['date']} is in the future: YNAB only records transactions that happened."
            )
        category = item.get("category_id")
        if category and category not in categories:
            raise ToolError(
                f"Category {category} is not in this budget: "
                "use a category_id from get_category_balances."
            )


@mcp.tool(
    tags={WRITE_TAG},
    annotations={
        "title": "Create transactions",
        "read_only_hint": False,
        "destructive_hint": False,
        "idempotent_hint": False,
        "open_world_hint": True,
    },
)
async def create_transactions(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    budget_id: str,
    account_id: str,
    transactions: list[NewTransaction],
    ctx: Context,
    approved: bool = False,
    confirmation: str | None = None,
) -> CreateResult | InputRequiredResult:
    """Create transactions on an account, e.g. ones the bank import missed, after the user confirms.

    Each transaction: date (YYYY-MM-DD, not in the future), amount in currency
    units (negative for spending), payee_name, and optionally memo and
    category_id. They are created cleared and, unless approved is true, left for
    the user to approve in YNAB. undo_operation deletes them. Confirmation works
    as for apply_categories.

    Args:
        budget_id: YNAB budget UUID or 'last-used'.
        account_id: Account to add them to (from list_accounts).
        transactions: The transactions to create.
        approved: Skip YNAB's review step.
        confirmation: Code from a previous "confirmation_required" result.
    """
    logger.info("Tool called: create_transactions(n=%d)", len(transactions))
    accounts = {a["id"]: a["name"] for a in await client.get_accounts(budget_id)}
    if account_id not in accounts:
        raise ToolError(
            f"Account {account_id} is not in this budget: use an id from list_accounts."
        )
    categories = {c["id"]: c["name"] for c in await client.get_categories(budget_id)}
    _check_new(transactions, categories, app.today())
    preview: list[NewTransactionPreview] = [
        {
            "date": item["date"],
            "amount": item["amount"],
            "payee": item.get("payee_name", ""),
            "category": categories.get(item.get("category_id", "")),
            "memo": item.get("memo"),
        }
        for item in transactions
    ]
    result: CreateResult = {
        "status": "applied",
        "message": "",
        "account": accounts[account_id],
        "transactions": preview,
        "created_ids": [],
        "duplicate_import_ids": [],
        "confirmation": None,
        "operation_id": None,
    }
    lines = [
        f"- {p['date']} {p['payee']} {p['amount']:.2f} ({p['category'] or 'no category'})"
        for p in preview[:20]
    ]
    question = f"Create {len(preview)} transaction(s) on {accounts[account_id]}?\n" + "\n".join(
        lines
    )
    subject: dict[str, Any] = {"account": account_id, "items": transactions, "approved": approved}
    stop = await gate(ctx, budget_id, subject, question, confirmation)
    if stop is not None:
        return stop if isinstance(stop, InputRequiredResult) else {**result, **stop}
    created = await client.create_transactions(
        budget_id, account_id, [dict(item) for item in transactions], approved=approved
    )
    operation_id = journal.Journal(journal.default_path()).record(
        budget_id, "create", [], {"transaction_ids": created["transaction_ids"]}
    )
    return {
        **result,
        "message": f"Created. undo_operation with operation_id {operation_id} deletes them.",
        "created_ids": created["transaction_ids"],
        "duplicate_import_ids": created["duplicate_import_ids"],
        "operation_id": operation_id,
    }
