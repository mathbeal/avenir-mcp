---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Budgeted, spent (activity) and available (balance) per category for a month.

Use it for "how much is left in Groceries?" or to list every category's money.
Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. For the share of
each budget consumed use get_budget_vs_actual; for the month's totals,
get_monthly_summary. One YNAB request; changes nothing.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 1 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |
| `month` | string | nein | `"current"` | 'YYYY-MM-01' or 'current'. |
| `include_empty` | boolean | nein | `false` | Also list categories with no amount at all. |

## Rückgabe

`array of object`

| Feld | Typ | Beschreibung |
|---|---|---|
| `category_id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group. |
| `budgeted` | number | Amount assigned to the category this month. |
| `activity` | number | Amount spent (negative) or received in the category this month. |
| `balance` | number | Available at the end of the month: carried over, plus budgeted, plus activity. |

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget",
  "month": "2026-09-01"
}
```

Antwort auf dem Demo-Budget:

```json
[
  {
    "category_id": "cat-rent",
    "name": "Miete",
    "group": "Fixkosten",
    "budgeted": 950.0,
    "activity": -950.0,
    "balance": 0.0
  },
  {
    "category_id": "cat-power",
    "name": "Strom",
    "group": "Fixkosten",
    "budgeted": 64.2,
    "activity": -64.2,
    "balance": 0.0
  },
  {
    "category_id": "cat-internet",
    "name": "Internet",
    "group": "Fixkosten",
    "budgeted": 29.99,
    "activity": -29.99,
    "balance": 0.0
  },
  {
    "category_id": "cat-phone",
    "name": "Handy",
    "group": "Fixkosten",
    "budgeted": 19.99,
    "activity": -19.99,
    "balance": 0.0
  },
  "… 6 more"
]
```

## Fehler

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fehler von YNAB selbst kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Einen Monat auswerten](/avenir-mcp/de/guides/monthly-review/)
