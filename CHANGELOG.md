# Changelog

## Unreleased

- FastMCP 4 and the 2026-07-28 MCP protocol: on such connections a write returns an
  input request (SEP-2322) and the client calls again with the user's answer, bound to
  the preview it answers; older connections are still asked during the call.
  Confirmation is now a yes/no form, and an accepted form left unticked is a no.
- Python 3.14.7, latest dependencies (fastmcp 4.0.9, mypy 2.3, isort 9, pytest 9.1).
  Tests fail on any warning; CI tries Python 3.15 without blocking.
- Evaluation: a real agent against an invented demo budget, nine tasks, 9/9 passed.
- Fixed: a dismissed confirmation (MCP elicitation `cancel`, as headless clients send)
  counted as a refusal, so no write could go through; it now falls back to a
  confirmation code. An explicit `decline` still refuses.
- `AVENIR_MCP_YNAB_URL` points the server at another API, such as the demo budget.
- Resources: a usage guide, the budgets, and each budget's categories and accounts.
- Prompts: `classify_pending`, `monthly_review`, `reconcile`, `plan_next_month`.
  Tests keep the guide and the prompts from naming a tool that does not exist.
- `create_transactions` validates account, categories and dates, previews the
  transactions, confirms, leaves them for review in YNAB unless `approved`, and
  `undo_operation` deletes them. `create_category` confirms and refuses a name already
  in the group.
- Diagnostics: WARNING by default (`AVENIR_MCP_LOG_LEVEL`), and an expected tool
  error is logged on one line instead of a full traceback.
- `set_category_budget` previews the amount before and after, waits for confirmation,
  is journaled, and `undo_operation` restores the previous amount unless it moved
  since. Undo lives in its own module and handles every journaled kind.
- `get_monthly_summary` and `get_category_balances` answer in currency units with only
  what an agent needs (135 and 4,794 characters on a real month, instead of about
  92,000 each). A malformed `month` is refused with the expected format instead of
  YNAB's 404.
- Removed `get_uncategorized_transactions`, `suggest_category` and
  `classify_transaction`: `suggest_categories` and `apply_categories` do the same,
  paginated, previewed and undoable. The catalog is 17 tools.
- GitHub Actions quality workflow: lockfile, lint, types, tests at 100 % coverage,
  lexdrift against a baseline, typos, zizmor and pip-audit; no permissions, actions
  pinned by SHA.
- fastmcp 3.2.0 and pytest 9.0.3, which fix known advisories.
- Read-only by default: write tools are registered only with `AVENIR_MCP_WRITE=1`.
- Every tool declares MCP annotations (`readOnlyHint`, and for writes
  `destructiveHint` and `idempotentHint`); a test enforces it.
- The server is split into topic modules (`tools_*`, `confirm`, `app`).
- `forecast_balance`: project the balance month by month and name the first shortfall.
  Recurring charges come from the history, other spending and income from the last
  3 months' averages (what already happened this month is deducted), one-off amounts
  from the caller; all are returned as assumptions.
- Fixed: normalized payees kept the creditor's IBAN from direct-debit labels.
- `reconcile_account`: compare an account with the bank's balance. A gap is explained
  (pending transactions, the one matching the difference, likely duplicates over the
  last 60 days) and never adjusted silently; a matching account is marked reconciled
  after confirmation, and `undo_operation` reverts it.
- `update_category`: rename a category or move it to another group, after a confirmed
  preview.
- Fixed: a suggestion could point to a hidden or deleted category, shown as a bare id.
- Fixed: a payee that once paid you in made payments to it look like income; history
  is now learnt separately for money in and money out.
- `apply_categories`: assign categories to many transactions in one YNAB request,
  after a preview the user confirms (elicitation, or a single-use code bound to the
  exact changes). Every applied operation is journaled locally.
- `undo_operation`: revert the latest operation or a named one, leaving alone any
  transaction changed since.
- `suggest_categories`: every pending transaction in one paginated, read-only answer,
  with history-based suggestions and the category list, for two YNAB requests.
- Payees are compared without card prefixes, invoice dates, masked card numbers or
  references, so a merchant is recognised across its bank labels.
- Fixed: after the first load, the transaction list only held what had changed since,
  so suggestions never found any history.
- First public version of the server, extracted from a personal setup: 14 tools
  over the YNAB API, a stdio and HTTP entry point (`avenir-mcp`), and 100 % branch
  coverage.
