---
title: "get_budget_vs_actual"
description: "Return a budget-vs-actual breakdown with utilisation percentage per category."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Return a budget-vs-actual breakdown with utilisation percentage per category.

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
| `month` | string | no | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Returns

`array of object`


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
    "id": "cat-rent",
    "name": "Rent",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Electricity",
    "budgeted": 70.0,
    "actual": 0.0,
    "balance": 70.0,
    "utilization_pct": 0.0
  },
  {
    "id": "cat-phone",
    "name": "Phone",
    "budgeted": 20.0,
    "actual": 19.99,
    "balance": 0.01,
    "utilization_pct": 99.9
  },
  {
    "id": "cat-groceries",
    "name": "Groceries",
    "budgeted": 400.0,
    "actual": 0.0,
    "balance": 400.0,
    "utilization_pct": 0.0
  },
  "… 5 more"
]
```

## Errors

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
