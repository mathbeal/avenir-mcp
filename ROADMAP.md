# Roadmap

avenir-mcp starts as a thin layer over the YNAB API. The goal is a server designed
for agents: fewer tools, each one a task; read-only by default; every write
previewed, confirmed and undoable; short, structured answers.

Newest first.

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
