---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Budgeted, spent (activity) and available (balance) per category for a month.

Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. Use
get_budget_vs_actual for the share of each budget consumed.

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
| `include_empty` | boolean | nee | `false` | Also list categories with no amount at all. |

## Resultaat

`array of object`

| Veld | Type | Beschrijving |
|---|---|---|
| `category_id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group. |
| `budgeted` | number | Amount assigned to the category this month. |
| `activity` | number | Amount spent (negative) or received in the category this month. |
| `balance` | number | Available at the end of the month: carried over, plus budgeted, plus activity. |

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
    "category_id": "cat-rent",
    "name": "Huur",
    "group": "Vaste lasten",
    "budgeted": 950.0,
    "activity": -950.0,
    "balance": 0.0
  },
  {
    "category_id": "cat-power",
    "name": "Stroom",
    "group": "Vaste lasten",
    "budgeted": 70.0,
    "activity": 0.0,
    "balance": 70.0
  },
  {
    "category_id": "cat-phone",
    "name": "Telefoon",
    "group": "Vaste lasten",
    "budgeted": 20.0,
    "activity": -19.99,
    "balance": 0.01
  },
  {
    "category_id": "cat-groceries",
    "name": "Boodschappen",
    "group": "Dagelijks",
    "budgeted": 400.0,
    "activity": 0.0,
    "balance": 400.0
  },
  "… 5 more"
]
```

## Fouten

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fouten van YNAB zelf komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Een maand doornemen](/avenir-mcp/nl/guides/monthly-review/)
