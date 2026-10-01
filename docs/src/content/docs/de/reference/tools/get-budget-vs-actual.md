---
title: "get_budget_vs_actual"
description: "Share of each category's budget spent in a month, to see what is over or close."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Share of each category's budget spent in a month, to see what is over or close.

Use it for "am I over budget?" or "which categories are nearly used up?".
Amounts in currency units, spending as a positive number; utilization_pct above
100 means over budget. For what is still available in each category use
get_category_balances; for the month's totals, get_monthly_summary; for several
months, get_spending_trends. One YNAB request; changes nothing.

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
| `month` | string | nein | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Rückgabe

`array of object`

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group, e.g. Fun for Tennis. |
| `budgeted` | number | Amount assigned to the category this month. |
| `actual` | number | Amount spent this month, as a positive number. |
| `balance` | number | What is left: budgeted minus spent, plus what was carried over; negative when overspent. |
| `utilization_pct` | number | Spent as a share of budgeted, in percent; above 100 means overspent, 0 when nothing is budgeted. |

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
    "id": "cat-rent",
    "name": "Miete",
    "group": "Fixkosten",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Strom",
    "group": "Fixkosten",
    "budgeted": 64.2,
    "actual": 64.2,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-internet",
    "name": "Internet",
    "group": "Fixkosten",
    "budgeted": 29.99,
    "actual": 29.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-phone",
    "name": "Handy",
    "group": "Fixkosten",
    "budgeted": 19.99,
    "actual": 19.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  "… 6 more"
]
```

## Fehler

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fehler von YNAB selbst kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Einen Monat auswerten](/avenir-mcp/de/guides/monthly-review/)
