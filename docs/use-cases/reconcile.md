# Reconcile an account

**Goal:** make sure YNAB agrees with your bank, and find out why when it does not.

## Ask

> My bank shows 3,440.80 on my checking account. Does YNAB agree?

or run the `reconcile` prompt with the account and the balance.

## What happens

**`reconcile_account`** compares the balance you give with YNAB's *cleared* balance.
If they differ, **nothing is written**: the answer explains the gap.

```json
--8<-- "snippets/reconcile_gap.json"
```

Here YNAB counts 71.86 more than the bank, and `possible_duplicates` points at two
identical Market Fresh payments two days apart: an import that came twice. The
answer can also point at a pending transaction whose amount equals the difference
(`explained_by`) and list what the bank has not shown yet (`uncleared`).

Fix the cause with Claude — delete the duplicate in YNAB, clear a transaction — and
ask again. When the balances match, Avenir previews the reconciliation: every
cleared transaction is marked *reconciled* once you confirm.

!!! question "What if the gap cannot be explained?"
    Ask for it explicitly: `adjust=true` records the remaining difference as a
    *Balance adjustment* transaction in Ready to Assign. It is never done on its own,
    because an adjustment hides a problem instead of solving it.

## Undo

`undo_operation` puts reconciled transactions back to *cleared* and deletes the
adjustment, if one was made.
