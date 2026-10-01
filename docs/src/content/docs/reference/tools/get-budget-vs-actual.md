---
title: "get_budget_vs_actual"
description: "Share of each category's budget spent in a month, to see what is over or close."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Share of each category's budget spent in a month, to see what is over or close.

Use it for "am I over budget?" or "which categories are nearly used up?".
Amounts in currency units, spending as a positive number; utilization_pct above
100 means over budget. For what is still available in each category use
get_category_balances; for the month's totals, get_monthly_summary; for several
months, get_spending_trends. One YNAB request; changes nothing.

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
| `month` | string | no | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Returns

`array of object`

| Field | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group, e.g. Fun for Tennis. |
| `budgeted` | number | Amount assigned to the category this month. |
| `actual` | number | Amount spent this month, as a positive number. |
| `balance` | number | What is left: budgeted minus spent, plus what was carried over; negative when overspent. |
| `utilization_pct` | number | Spent as a share of budgeted, in percent; above 100 means overspent, 0 when nothing is budgeted. |

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
    "id": "cat-rent",
    "name": "Rent",
    "group": "Bills",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Electricity",
    "group": "Bills",
    "budgeted": 64.2,
    "actual": 64.2,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-internet",
    "name": "Internet",
    "group": "Bills",
    "budgeted": 29.99,
    "actual": 29.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-phone",
    "name": "Phone",
    "group": "Bills",
    "budgeted": 19.99,
    "actual": 19.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  "… 6 more"
]
```

## Errors

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
