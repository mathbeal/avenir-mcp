---
title: "get_budget_vs_actual"
description: "Share of each category's budget spent in a month, to see what is over or close."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Share of each category's budget spent in a month, to see what is over or close.

Use it for "am I over budget?" or "which categories are nearly used up?".
Amounts in currency units, spending as a positive number; utilization_pct above
100 means over budget. For what is still available in each category use
get_category_balances; for the month's totals, get_monthly_summary; for several
months, get_spending_trends. One YNAB request; changes nothing.

## Comportement

| | |
|---|---|
| Nature | lecture seule |
| Confirmation | non |
| Annulation | non |
| Idempotent | oui |
| Requêtes YNAB | 1 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `plan_id` | string | oui | — | YNAB plan id or 'last-used'. |
| `month` | string | non | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Retour

`array of object`

| Champ | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group, e.g. Fun for Tennis. |
| `budgeted` | number | Amount assigned to the category this month. |
| `actual` | number | Amount spent this month, as a positive number. |
| `balance` | number | What is left: budgeted minus spent, plus what was carried over; negative when overspent. |
| `utilization_pct` | number | Spent as a share of budgeted, in percent; above 100 means overspent, 0 when nothing is budgeted. |

## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget",
  "month": "2026-09-01"
}
```

Réponse sur le budget de démonstration :

```json
[
  {
    "id": "cat-rent",
    "name": "Loyer",
    "group": "Charges fixes",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Électricité",
    "group": "Charges fixes",
    "budgeted": 64.2,
    "actual": 64.2,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-internet",
    "name": "Box internet",
    "group": "Charges fixes",
    "budgeted": 29.99,
    "actual": 29.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-phone",
    "name": "Téléphone",
    "group": "Charges fixes",
    "budgeted": 19.99,
    "actual": 19.99,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  "… 6 more"
]
```

## Erreurs

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Faire le point sur un mois](/avenir-mcp/fr/guides/monthly-review/)
