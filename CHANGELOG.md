# Changelog

## Unreleased

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
