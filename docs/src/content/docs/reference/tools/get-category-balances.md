---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Budgeted, spent (activity) and available (balance) per category for a month.

Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. Use
get_budget_vs_actual for the share of each budget consumed.

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
| `month` | string | no | `"current"` | 'YYYY-MM-01' or 'current'. |
| `include_empty` | boolean | no | `false` | Also list categories with no amount at all. |

## Returns

`array of object`

| Field | Type | Description |
|---|---|---|
| `category_id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group. |
| `budgeted` | number | Amount assigned to the category this month. |
| `activity` | number | Amount spent (negative) or received in the category this month. |
| `balance` | number | Available at the end of the month: carried over, plus budgeted, plus activity. |

## Example

Arguments:

```json
{
  "budget_id": "demo-budget",
  "month": "2026-09-01"
}
```

Answer on the demo budget:

```json
[
  {
    "category_id": "cat-rent",
    "name": "Rent",
    "group": "Bills",
    "budgeted": 950.0,
    "activity": -950.0,
    "balance": 0.0
  },
  {
    "category_id": "cat-power",
    "name": "Electricity",
    "group": "Bills",
    "budgeted": 70.0,
    "activity": 0.0,
    "balance": 70.0
  },
  {
    "category_id": "cat-phone",
    "name": "Phone",
    "group": "Bills",
    "budgeted": 20.0,
    "activity": -19.99,
    "balance": 0.01
  },
  {
    "category_id": "cat-groceries",
    "name": "Groceries",
    "group": "Everyday",
    "budgeted": 400.0,
    "activity": 0.0,
    "balance": 400.0
  },
  "… 5 more"
]
```

## Errors

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
