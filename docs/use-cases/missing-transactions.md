# Add missing transactions

**Goal:** record what the bank import missed — a pharmacy payment, a cash expense.

## Ask

> Add a payment of 32.40 to Pharmacie Centrale on September 21, not imported by the bank.

## What happens

**`create_transactions`** checks the account, the categories and the dates (not in
the future), then previews what it will add:

```json
--8<-- "snippets/create_preview.json"
```

Once you confirm, the transactions are created **cleared** and, unless you ask for
`approved`, left for you to review in YNAB like any import. `undo_operation` deletes
them.
