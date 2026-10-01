---
title: "get_monthly_summary"
description: "A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

Amounts in currency units; activity is negative for spending. Only
overspent categories are listed; use get_category_balances for all of them.

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

## Rückgabe

| Feld | Typ | Beschreibung |
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
      "group": "Alltag",
      "balance": -22.5
    }
  ]
}
```

## Fehler

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Fehler von YNAB selbst kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Einen Monat auswerten](/avenir-mcp/de/guides/monthly-review/)
