# Roadmap

avenir-mcp starts as a thin layer over the YNAB API. The goal is a server designed
for agents: fewer tools, each one a task; read-only by default; every write
previewed, confirmed and undoable; short, structured answers.

Newest first.

## What comparable servers offer, and what follows from it

Surveyed on 2026-09-29, on the public YNAB MCP servers with the most use (not named
here: the point is what they offer, not who). They fall in three families:

- **API mirrors**: one tool per endpoint. Complete, but the agent does
  the work and pays for it in context; writes are not previewed.
- **Wide toolboxes**, up to some sixty tools: budget moves, auto
  assign, transaction edits and deletes, file import, spending by payee, cash flow, net
  worth, savings opportunities, spending pace.
- **Task servers**: recurring
  and subscription detection, budget health, credit-card audit, merged categories,
  money movements, undo history, write modes, receipts.

avenir-mcp stays on its line (fewer tools, each a task; every write previewed,
confirmed and undoable; local only). Measured against that line, the gaps worth
closing, in order of value per tool added:

1. **Move money between categories** (`move_money`, one confirmation, one undo). *In
   review.* The first gesture of a monthly review; every toolbox above has it.
2. **Import from linked accounts** (`import_transactions`). *In review.*
3. **Subscriptions and recurring charges** as a read-only answer. `forecast.recurring`
   already finds them for the projection; exposing them answers "what am I subscribed
   to, and what did it cost this year?" with no new YNAB request.
4. **Payees**: list, and rename a bank label into the merchant's name (`getPayees`,
   `updatePayee`, already planned). Renaming at the source improves every suggestion.
5. **Scheduled transactions and targets**: the section below.
6. **Edit a transaction** (date, amount, payee, memo). Needs a decision first: undo would
   have to keep the old memo and payee in the journal, which today holds identifiers
   and budgeted amounts only. Either the journal keeps them (said on the privacy page),
   or edits stay without undo, like `approve_transactions`.
7. **Money movements** in the monthly review (`getMoneyMovements`, planned): what was
   moved between categories this month, and when.

Left out on purpose: an endpoint-per-tool mirror; hosted OAuth for other people's
plans (YNAB's terms, and the server is local); net worth and "savings opportunities"
scores, which an agent computes better from `list_accounts` and the trends than a fixed
formula does.

## Next: from a document to the year's schedules

- The user gives the agent a document that sets future payments: a tax notice, a
  corrected tax schedule, a building's call for funds, a loan's amortisation table.
  The agent reads it; avenir-mcp never parses a document.
- Write tools for scheduled transactions: create, change and delete, each previewed,
  confirmed and undoable.
- A tool to set a category's target: amount, and date for a one-off need.
- One batch per document: a single preview of every schedule and target to create or
  change, one confirmation, one `undo_operation`.
- A new document updates the schedules it replaces instead of adding duplicates,
  matched by payee as `forecast.is_scheduled` does.
- The answer says what was created, changed or left out, and why: YNAB refuses a date
  in the past or more than five years ahead, and a category on an inflow.

## 1.0: verified and published

- Contract tests through the MCP protocol, and an MCP Inspector session in CI.
- An evaluation suite run by a real agent on a demo budget. *Done: 10 tasks, 10/10.*
- Tooling: ruff, 100 % branch coverage, mutation testing, hardened GitHub Actions,
  pip-audit, Python 3.11–3.14.
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
