# Roadmap

avenir-mcp starts as a thin layer over the YNAB API. The goal is a server designed
for agents: fewer tools, each one a task; read-only by default; every write
previewed, confirmed and undoable; short, structured answers.

This file says what the project intends to do over the next twelve months, to
October 2027, and what it will not do. The order is the intended one, not a promise of
dates; when plans change, this file changes with them. Past milestones follow,
newest first.

## The next twelve months

### Reports that answer a question about the future

Read-only tools, each one a question a user asks about their money, computed from the
plan as the existing reports are:

- `get_net_worth_trend`: net worth month by month, assets and debts apart. *Done.*
- `get_runway`: how many months the money available would cover usual spending. *Done.*
- `get_savings_rate`: the share of income kept each month, and its trend. *Done.*
- `get_underfunded_targets`: the categories whose target is not met this month, and
  what each still needs. *Done.*
- `get_debt_payoff_plan`: when each debt is paid off at the current payments, and with
  an extra amount. *Done.*
- `get_age_of_money`: how YNAB's Age of Money changed month by month. *Done.*

### Payees named as the user names them

- `list_payees`: every payee of the plan with the merchant its bank label normalises
  to, and how often it is used. *Done.*
- `rename_payee`: one bank label becomes the merchant's name, for the whole history it
  carries, previewed, confirmed and undoable. *Done.*

### From a document to the year's schedules

See the section below: write tools for scheduled transactions, one confirmed batch per
document.

### What YNAB's API offers and avenir-mcp does not use yet

The operations marked "planned" in `api/coverage.toml`, each in a task: the plan's
currency, to show amounts with it; money moved between categories, for the monthly
review; category groups; editing one transaction.

### Around the server

- A `.mcpb` bundle for one-click install in Claude Desktop.
- Undo for `update_category`.
- The evaluation run through other clients than Claude Code, and with local models.
- A second maintainer (see [GOVERNANCE.md](GOVERNANCE.md)).

## What avenir-mcp will not do

- **Move real money.** It changes a YNAB plan, never a bank account: no payment, no
  transfer between banks.
- **Act without the user.** No write without a preview and the user's confirmation,
  apart from marking transactions reviewed and asking YNAB to import from linked banks;
  no automatic schedule, no background job.
- **Serve several people.** No hosted or shared server, no user accounts: YNAB's terms
  require OAuth for an application used by others.
- **Give financial advice.** It reports and projects what the plan holds; the decisions
  stay with the user.
- **Read documents.** The agent reads a tax notice or a statement; avenir-mcp receives
  what the agent extracted.
- **Send data elsewhere.** No telemetry, no analytics, no service other than YNAB's API
  and the once-a-day version check on PyPI.
- **Wrap every endpoint.** An operation of YNAB's API becomes part of a tool only when a
  task needs it; `api/coverage.toml` gives the reason for each one left out, such as the
  locations of payees, which no task needs.
- **Replace YNAB's app.** Accounts are opened, bank links fixed and categories deleted
  in YNAB.

## In progress: from a document to the year's schedules

- The user gives the agent a document that sets future payments: a tax notice, a
  corrected tax schedule, a building's call for funds, a loan's amortisation table.
  The agent reads it; avenir-mcp never parses a document.
- Write tools for scheduled transactions: create, change and delete, each previewed,
  confirmed and undoable.
- A tool to set a category's target: amount, and date for a one-off need. *Done
  (`set_category_target`).*
- One batch per document: a single preview of every schedule and target to create or
  change, one confirmation, one `undo_operation`.
- A new document updates the schedules it replaces instead of adding duplicates,
  matched by payee as `forecast.is_scheduled` does.
- The answer says what was created, changed or left out, and why: YNAB refuses a date
  in the past or more than five years ahead, and a category on an inflow.

## 1.0: verified and published

- Contract tests through the MCP protocol, and an MCP Inspector session in CI.
- An evaluation suite run by a real agent on a demo budget. *Done: 26 tasks, 26/26.*
- Tooling: ruff, 100 % branch coverage, mutation testing, hardened GitHub Actions,
  pip-audit, Python 3.12–3.15.
- PyPI release through Trusted Publishing, a generated changelog, a `.mcpb` bundle for
  Claude Desktop.

## Done since 0.5

- `forecast_balance`: month-by-month projection with visible assumptions.

## 0.5: tasks, not endpoints

- `reconcile_account`: bank balance in, discrepancy and adjustment out, with a preview. *Done.*
- Better category suggestions: normalised payee names, learning from past decisions.
- MCP resources (categories, accounts, a YNAB method guide) and prompts (monthly review,
  classify pending transactions, reconcile an account, plan next month). *Done.*

## 0.4: security and API budget

- Transaction text delimited and truncated as untrusted data.
- HTTP transport: `Origin` validation, optional local bearer token, localhost only.
- A request counter for YNAB's 200 requests/hour, retry on 429, caching, delta sync everywhere.
- Batch category suggestions from a single history download. *Done (`suggest_categories`).*

## 0.3: safe writes

- Tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) on every tool, enforced by a test. *Done.*
- Read-only by default: write tools are not even registered unless enabled. *Done.*
- Preview → confirmation (MCP elicitation, or a single-use token bound to the preview) → apply.
  *Done for categories (`apply_categories`).*
- A local journal of applied writes and an `undo` tool. What cannot be undone is documented.
  *Done for categories (`undo_operation`).*
- Created transactions left unapproved by default.

## 0.2: tools that respect the context window

- Amounts in euros (decimal) everywhere; milliunits stay inside the HTTP client.
- Typed outputs: a precise `outputSchema` and matching `structuredContent` for every tool.
- Bounded answers: filters, opaque `cursor` pagination, `response_format` (`concise` / `detailed`).
- Actionable errors: parameters validated before calling YNAB, messages that say what to fix.
- Tool names prefixed `ynab_`, descriptions written for an agent, a default budget.
