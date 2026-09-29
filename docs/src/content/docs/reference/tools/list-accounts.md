---
title: "list_accounts"
description: "List the plan's accounts with their balances, bank link and last reconciliation."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

List the plan's accounts with their balances, bank link and last reconciliation.

Use it to reconcile YNAB with the bank, and to tell the user when a bank link is
broken (no transaction comes in until they fix it in YNAB) or when an account has
not been reconciled for months. Balances are in currency units.

## Behaviour

| | |
|---|---|
| Kind | read-only |
| Confirmation | no |
| Undo | no |
| Idempotent | yes |
| YNAB requests | 1 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `plan_id` | string | yes | — | YNAB plan id or 'last-used'. |

## Returns

`array of object`

| Field | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the account. |
| `name` | string | Account name. |
| `type` | string | YNAB account type, e.g. checking, savings, creditCard, otherAsset. |
| `on_budget` | boolean | False for a tracking account, whose transactions take no category. |
| `closed` | boolean | True when the account is closed in YNAB. |
| `balance` | number | Balance of all transactions. |
| `cleared_balance` | number | Balance of the transactions the bank has shown. |
| `uncleared_balance` | number | Balance of the transactions the bank has not shown yet. |
| `bank_link` | "healthy" \| "broken" \| "none" | Whether YNAB imports this account from the bank: broken means the connection needs the user's attention in YNAB, and no new transaction will come in until then. |
| `last_reconciled` | string \| null | Date (YYYY-MM-DD) of the last reconciliation, or None if never reconciled. |

## Example

Arguments:

```json
{
  "plan_id": "demo-budget"
}
```

Answer on the demo budget:

```json
[
  {
    "id": "acc-checking",
    "name": "Checking",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3512.66,
    "cleared_balance": 3512.66,
    "uncleared_balance": 0.0,
    "bank_link": "healthy",
    "last_reconciled": "2026-08-31"
  },
  {
    "id": "acc-savings",
    "name": "Savings",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  }
]
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
