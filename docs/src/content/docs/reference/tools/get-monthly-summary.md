---
title: "get_monthly_summary"
description: "A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

Amounts in currency units; activity is negative for spending. Only
overspent categories are listed; use get_category_balances for all of them.

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

## Returns

| Field | Type | Description |
|---|---|---|
| `month` | string | First day of the month, YYYY-MM-01. |
| `income` | number | Money received in the month and assigned to Ready to Assign. |
| `budgeted` | number | Total assigned to categories in the month. |
| `activity` | number | Total spent (negative) and received in categories during the month. |
| `ready_to_assign` | number | Money not yet given a job; negative when more was assigned than received. |
| `age_of_money` | integer \| null | Days between receiving money and spending it, as YNAB computes it; null when unknown. |
| `overspent` | array of object | Categories whose available balance is negative this month. |
| `overspent[].category_id` | string | YNAB id of the category. |
| `overspent[].name` | string | Category name. |
| `overspent[].group` | string | Name of the category's group. |
| `overspent[].balance` | number | Available balance, negative: the amount overspent, in currency units. |

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
{
  "month": "2026-09-01",
  "income": 0.0,
  "budgeted": 1945.0,
  "activity": -1112.49,
  "ready_to_assign": 1820.0,
  "age_of_money": 18,
  "overspent": [
    {
      "category_id": "cat-restaurants",
      "name": "Restaurants",
      "group": "Everyday",
      "balance": -22.5
    }
  ]
}
```

## Errors

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
