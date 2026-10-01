---
title: "get_budget_vs_actual"
description: "Return a budget-vs-actual breakdown with utilisation percentage per category."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Return a budget-vs-actual breakdown with utilisation percentage per category.

Amounts in currency units; utilization_pct above 100 means over budget.

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
| `month` | string | nee | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Resultaat

`array of object`

| Veld | Type | Beschrijving |
|---|---|---|
| `id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group, e.g. Fun for Tennis. |
| `budgeted` | number | Amount assigned to the category this month. |
| `actual` | number | Amount spent this month, as a positive number. |
| `balance` | number | What is left: budgeted minus spent, plus what was carried over; negative when overspent. |
| `utilization_pct` | number | Spent as a share of budgeted, in percent; above 100 means overspent, 0 when nothing is budgeted. |

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
[
  {
    "id": "cat-rent",
    "name": "Huur",
    "group": "Vaste lasten",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Stroom",
    "group": "Vaste lasten",
    "budgeted": 64.2,
    "actual": 64.2,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-internet",
    "name": "Internet",
    "group": "Vaste lasten",
    "budgeted": 29.99,
    "actual": 29.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-phone",
    "name": "Telefoon",
    "group": "Vaste lasten",
    "budgeted": 19.99,
    "actual": 19.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  "… 6 more"
]
```

## Fouten

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fouten van YNAB zelf komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Een maand doornemen](/avenir-mcp/nl/guides/monthly-review/)
