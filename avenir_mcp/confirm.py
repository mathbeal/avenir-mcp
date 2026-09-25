"""Confirm a write with the user, then apply and journal it.

A client that supports elicitation asks the user: on a 2026-07-28 connection the
tool returns an input request and the client calls again with the answer; on an
older one the server asks during the call. Otherwise, or if the question was
dismissed, the call returns a preview and a single-use code bound to exactly
that preview.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal, TypedDict

from fastmcp import Context  # pylint: disable=import-error
from fastmcp.exceptions import ToolError  # pylint: disable=import-error
from fastmcp.server.elicitation import (  # pylint: disable=import-error
    handle_elicit_accept,
    parse_elicit_response_type,
)
from mcp import types  # pylint: disable=import-error
from mcp_types.version import MODERN_PROTOCOL_VERSIONS  # pylint: disable=import-error
from pydantic import ConfigDict, with_config  # pylint: disable=import-error

from avenir_mcp import client, journal, writes
from avenir_mcp.text import untrusted

logger = logging.getLogger(__name__)


CONFIRMATIONS = writes.Confirmations()

# A yes/no form: the client shows a checkbox the user must tick.
_YES_NO = parse_elicit_response_type(bool)
_QUESTION_KEY = "confirm"


WriteStatus = Literal["applied", "confirmation_required", "declined", "nothing_to_do"]


@with_config(ConfigDict(use_attribute_docstrings=True))
class WriteResult(TypedDict):
    """The outcome of a write tool."""

    status: WriteStatus
    """Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the
    user agrees), declined (the user said no), or nothing_to_do.
    """
    message: str
    """What happened and what to do next, for the agent to relay."""
    changes: list[writes.Change]
    """Every transaction that changes: before and after."""
    unchanged_count: int
    """Assignments that would change nothing and were skipped."""
    conflicts: list[str]
    """Ids left alone because they changed since the operation (undo only)."""
    confirmation: str | None
    """Single-use code confirming exactly this preview, valid 10 minutes; null unless status is
    confirmation_required.
    """
    operation_id: str | None
    """Journal id of the applied operation, for undo_operation; null unless status is applied."""


def result_of(status: WriteStatus, message: str, plan: writes.Plan, **extra: Any) -> WriteResult:
    """Build a write tool's result from a plan; `extra` may set confirmation and operation_id."""
    return {
        "status": status,
        "message": message,
        "changes": plan["changes"],
        "unchanged_count": plan["unchanged_count"],
        "conflicts": plan["conflicts"],
        "confirmation": extra.get("confirmation"),
        "operation_id": extra.get("operation_id"),
    }


def describe(plan: writes.Plan, action: str) -> str:
    """The question put to the user: the first 20 changes, and how many more."""
    lines = [
        f"- {c['date']} {untrusted(c['payee'])} {c['amount']:.2f}: "
        f"{untrusted(c['from_category']) or 'no category'} → "
        f"{untrusted(c['to_category']) or 'no category'}"
        for c in plan["changes"][:20]
    ]
    more = len(plan["changes"]) - len(lines)
    if more > 0:
        lines.append(f"- … and {more} more")
    return f"{action} {len(plan['changes'])} transaction(s)?\n" + "\n".join(lines)


def _answer(action: str, content: dict[str, Any] | None) -> WriteStatus | None:
    """Read the user's answer; None when nobody answered (the question was dismissed)."""
    if action == "accept":
        # An accepted form with the box left unticked is not a yes.
        return "applied" if handle_elicit_accept(_YES_NO, content).data is True else "declined"
    if action == "decline":
        return "declined"
    return None


def _spend_code(confirmation: str, budget_id: str, subject: object, required: bool) -> WriteStatus:
    """ "applied" when the code was issued for exactly this subject; otherwise an error."""
    if required:
        raise ToolError(
            "Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again "
            "without confirmation, and the user answers in the client."
        )
    if CONFIRMATIONS.consume(confirmation, budget_id, subject):
        return "applied"
    raise ToolError(
        "This confirmation code is unknown, expired, already used, or was issued for "
        "different changes. Call again without confirmation to get a new preview."
    )


def _modern_answer(
    ctx: Context, budget_id: str, subject: object, question: str
) -> WriteStatus | None | types.InputRequiredResult:
    """Protocol 2026-07-28: request the answer, or read the one the client sends back.

    The request state carries the preview's fingerprint: an answer to a preview of
    other changes is refused.
    """
    fingerprint = writes.fingerprint(budget_id, subject)
    responses = ctx.input_responses
    if not responses or _QUESTION_KEY not in responses:
        request = types.ElicitRequest(
            params=types.ElicitRequestFormParams(message=question, requested_schema=_YES_NO.schema)
        )
        return types.InputRequiredResult(
            input_requests={_QUESTION_KEY: request}, request_state=fingerprint
        )
    if ctx.request_state != fingerprint:
        raise ToolError(
            "The budget changed between the preview and the answer. "
            "Call again without an answer to get a new preview."
        )
    reply = responses[_QUESTION_KEY]
    return _answer(reply.action, reply.content) if isinstance(reply, types.ElicitResult) else None


async def _answer_in_client(
    ctx: Context, budget_id: str, subject: object, question: str
) -> WriteStatus | None | types.InputRequiredResult:
    """The user's answer given in the client; None when nobody answered."""
    rc = ctx.request_context
    if rc is not None and rc.protocol_version in MODERN_PROTOCOL_VERSIONS:
        return _modern_answer(ctx, budget_id, subject, question)
    answer = await ctx.elicit(question, bool)
    return _answer(answer.action, {"value": getattr(answer, "data", None)})


async def ask(
    ctx: Context, budget_id: str, subject: object, question: str, confirmation: str | None
) -> WriteStatus | str | types.InputRequiredResult:
    """Return "applied" when the user agreed, "declined", a code to confirm later, or
    an input request the tool must return so the client can ask (2026-07-28).

    `subject` is the exact change being confirmed: a code, or an answer, only ever
    confirms it.

    With AVENIR_MCP_REQUIRE_ELICITATION=1 only the user's answer in the client counts:
    an agent could relay a code without asking, so codes are neither issued nor accepted.
    """
    required = os.getenv("AVENIR_MCP_REQUIRE_ELICITATION") == "1"
    if confirmation is not None:
        return _spend_code(confirmation, budget_id, subject, required)
    can_ask = ctx.session.check_client_capability(
        types.ClientCapabilities(elicitation=types.ElicitationCapability())
    )
    if not can_ask and required:
        raise ToolError(
            "This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 "
            "forbids confirmation codes: nothing was changed. Use a client that supports MCP "
            "elicitation, or unset the variable."
        )
    if not can_ask:
        return CONFIRMATIONS.issue(budget_id, subject)
    decision = await _answer_in_client(ctx, budget_id, subject, question)
    if decision is not None:
        return decision
    # Nobody said no when the question was dismissed: fall back to a code, unless
    # only an answer in the client may confirm.
    return "declined" if required else CONFIRMATIONS.issue(budget_id, subject)


async def write_plan(
    ctx: Context,
    budget_id: str,
    plan: writes.Plan,
    action: str,
    confirmation: str | None,
) -> tuple[WriteResult | types.InputRequiredResult, str | None]:
    """Confirm and apply a plan; return the result and the new operation id."""
    if not plan["changes"]:
        message = "Nothing to change." + (
            f" {len(plan['conflicts'])} transaction(s) changed since and were left alone."
            if plan["conflicts"]
            else ""
        )
        return result_of("nothing_to_do", message, plan), None
    decision = await ask(ctx, budget_id, plan["changes"], describe(plan, action), confirmation)
    if isinstance(decision, types.InputRequiredResult):
        return decision, None
    if decision == "declined":
        return result_of("declined", "The user declined: nothing was changed.", plan), None
    if decision != "applied":
        message = (
            "Nothing changed yet. Show these changes to the user; if they agree, call "
            "again with the same arguments and this confirmation code (valid 10 minutes)."
        )
        return result_of("confirmation_required", message, plan, confirmation=decision), None
    await client.set_transaction_categories(
        budget_id, [(c["transaction_id"], c["to_category_id"]) for c in plan["changes"]]
    )
    moves: list[journal.Move] = [
        {
            "transaction_id": c["transaction_id"],
            "from_category_id": c["from_category_id"],
            "to_category_id": c["to_category_id"],
        }
        for c in plan["changes"]
    ]
    operation_id = journal.Journal(journal.default_path()).record(budget_id, "categorize", moves)
    message = f"Applied. undo_operation with operation_id {operation_id} reverts it."
    result = result_of("applied", message, plan, operation_id=operation_id)
    return result, operation_id


@with_config(ConfigDict(use_attribute_docstrings=True))
class NotApplied(TypedDict):
    """Why a confirmed write did not happen, in a tool result's own fields."""

    status: WriteStatus
    """declined or confirmation_required."""
    message: str
    """What happened and what to do next, for the agent to relay."""
    confirmation: str | None
    """Single-use code confirming exactly this preview, valid 10 minutes; null unless status is
    confirmation_required.
    """


def not_applied(decision: WriteStatus | str, question: str) -> NotApplied | None:
    """Turn ask()'s answer into result fields, or None when the write may proceed."""
    if decision == "applied":
        return None
    if decision == "declined":
        return {
            "status": "declined",
            "message": "The user declined: nothing changed.",
            "confirmation": None,
        }
    return {
        "status": "confirmation_required",
        "message": (
            f"Nothing changed yet. {question} If the user agrees, call again with this code."
        ),
        "confirmation": decision,
    }


async def gate(
    ctx: Context, budget_id: str, subject: object, question: str, confirmation: str | None
) -> NotApplied | types.InputRequiredResult | None:
    """Ask for confirmation; None when the write may proceed, otherwise what to return.

    A tool returns an InputRequiredResult as is, and merges NotApplied fields
    into its own result.
    """
    decision = await ask(ctx, budget_id, subject, question, confirmation)
    if isinstance(decision, types.InputRequiredResult):
        return decision
    return not_applied(decision, question)
