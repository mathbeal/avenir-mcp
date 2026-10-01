---
title: "get_monthly_summary"
description: "A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

Use it first to review a month. Amounts in currency units; activity is negative
for spending. Only overspent categories are listed: use get_category_balances
for all of them, get_spending_trends to compare with earlier months, and
forecast_balance for the months ahead. One YNAB request; changes nothing.

## Gedrag

| | |
|---|---|
| Soort | alleen lezen |
| Bevestiging | nee |
| Ongedaan maken | nee |
| Idempotent | ja |
| YNAB-verzoeken | 1 voor het voorbeeld hieronder, lege cache |

## Parameters

| Naam | Type | Verplicht | Standaard | Beschrijving |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |
| `month` | string | nee | `"current"` | 'YYYY-MM-01' or 'current'. |

## Resultaat

| Veld | Type | Beschrijving |
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

## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget",
  "month": "2026-09-01"
}
```

Antwoord op het demobudget:

```json
{
  "month": "2026-09-01",
  "income": 0.0,
  "budgeted": 1967.67,
  "activity": -1206.68,
  "ready_to_assign": 1729.32,
  "age_of_money": 18,
  "overspent": [
    {
      "category_id": "cat-restaurants",
      "name": "Restaurants",
      "group": "Dagelijks",
      "balance": -22.5
    }
  ]
}
```

## Fouten

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fouten van YNAB zelf komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Een maand doornemen](/avenir-mcp/nl/guides/monthly-review/)
