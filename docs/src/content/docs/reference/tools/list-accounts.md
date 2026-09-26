---
title: "list_accounts"
description: "List the budget's accounts with their current balances (in currency units)."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

List the budget's accounts with their current balances (in currency units).

Use it to reconcile YNAB with the bank.

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
| `budget_id` | string | yes | — | YNAB budget UUID or 'last-used'. |

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

## Example

Arguments:

```json
{
  "budget_id": "demo-budget"
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
    "uncleared_balance": 0.0
  },
  {
    "id": "acc-savings",
    "name": "Savings",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0
  }
]
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
