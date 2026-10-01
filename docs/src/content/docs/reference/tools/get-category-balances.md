---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Budgeted, spent (activity) and available (balance) per category for a month.

Use it for "how much is left in Groceries?" or to list every category's money.
Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. For the share of
each budget consumed use get_budget_vs_actual; for the month's totals,
get_monthly_summary. One YNAB request; changes nothing.

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
  "plan_id": "demo-budget",
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
    "budgeted": 64.2,
    "activity": -64.2,
    "balance": 0.0
  },
  {
    "category_id": "cat-internet",
    "name": "Internet",
    "group": "Bills",
    "budgeted": 29.99,
    "activity": -29.99,
    "balance": 0.0
  },
  {
    "category_id": "cat-phone",
    "name": "Phone",
    "group": "Bills",
    "budgeted": 19.99,
    "activity": -19.99,
    "balance": 0.0
  },
  "… 6 more"
]
```

## Errors

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
