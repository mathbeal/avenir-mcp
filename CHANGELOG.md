# Changelog

## Unreleased

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
