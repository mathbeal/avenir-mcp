# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What vulture cannot see is alive, and why.

`just lint` runs vulture at full sensitivity: it reports every name no other line of
the repository reads. Something a framework calls, or that pydantic reads when it
serialises a result, looks exactly like dead code to it. Each name below is such a
case, with the proof it is alive; anything else vulture reports is dead code to
remove, not a line to add here.

Vulture reads this file as code, so a bare `_.attribute` counts as a read of
`attribute`. The module is never imported or run: `_` is deliberately undefined.
Functions registered by `@mcp.tool`, `@mcp.resource`, `@mcp.prompt` and
`@pytest.fixture` need no entry at all; the decorator is the proof, and `just lint`
passes those four to `--ignore-decorators` so that a new tool or fixture never has to
be whitelisted.
"""

# --------------------------------------------------------------------------------
# Fields of pydantic models.
#
# A tool result derives from `avenir_mcp.model.Model`: pydantic reads each field when
# it serialises the result an agent receives, and the field's docstring becomes its
# description in the schema. No line of the repository names them, and the protocol
# tests check them through the JSON, not by attribute. Removing one would change the
# interface agents see.
# --------------------------------------------------------------------------------

months_looked_at  # avenir_mcp/charges.py: RecurringCharges, the months searched
applied_at  # avenir_mcp/journal.py: JournalEntry, when the write was applied
scheduled_id  # avenir_mcp/schedule.py: YNAB's id of the scheduled transaction
assumptions  # avenir_mcp/tools_accounts.py: ForecastBalance, what the projection assumed
created_ids  # avenir_mcp/tools_accounts.py: ids of the transactions created
duplicate_import_ids  # avenir_mcp/tools_accounts.py: import ids YNAB refused
last_month  # avenir_mcp/tools_budget.py: last month of the plan with data
uncleared_balance  # avenir_mcp/tools_budget.py: balance the bank has not shown yet
bank_link  # avenir_mcp/tools_budget.py: whether YNAB still imports from the bank
last_reconciled  # avenir_mcp/tools_budget.py: date of the last reconciliation
transaction_ids  # avenir_mcp/tools_budget.py: ids of the transactions imported
available_after  # avenir_mcp/tools_categories.py: what a move leaves available
undoable  # avenir_mcp/tools_targets.py: whether YNAB's API can bring the target back
percent_complete  # avenir_mcp/underfunded.py: how far along the target is

# `extra="forbid"` and `use_attribute_docstrings=True` on every model
# (avenir_mcp/model.py), `extra="ignore"` on a journal line written by a later version
# (avenir_mcp/journal.py): pydantic reads the name on the class itself.
model_config

# --------------------------------------------------------------------------------
# Hooks a framework calls.
# --------------------------------------------------------------------------------

# avenir_mcp/app.py: FastMCP calls this on `_WriteGate`, the transform that hides the
# write tools while writes are off; it overrides `fastmcp.server.transforms.Transform`.
_.get_tool

# avenir_mcp/app.py: `QuietToolErrors` is a `logging.Filter`; it rewrites these two
# attributes of the record, and the standard library's formatter reads them when it
# emits the line.
_.msg
_.exc_text

# evals/fake_ynab.py: `Handler` derives from `http.server.BaseHTTPRequestHandler`,
# which dispatches a request to `do_<METHOD>` and sends every log line through
# `log_message` (overridden so the stand-in stays quiet).
_.log_message
_.do_GET
_.do_PATCH
_.do_POST
_.do_DELETE

# tests/test_ynab_terms.py: pytest reads the module's `pytestmark` to mark every test
# of the file `ynab_terms`, so `pytest -m ynab_terms` finds them.
pytestmark

# --------------------------------------------------------------------------------
# Attributes set on a test double.
# --------------------------------------------------------------------------------

# tests/test_client.py: the fake `httpx.AsyncClient` is used with `async with`, which
# calls `__aexit__`; `side_effect` makes a mocked `response.json()` raise, as a
# non-JSON error page from YNAB does. unittest.mock reads both.
_.__aexit__
_.side_effect
