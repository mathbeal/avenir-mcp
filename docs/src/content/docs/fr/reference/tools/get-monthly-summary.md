---
title: "get_monthly_summary"
description: "A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

Use it first to review a month. Amounts in currency units; activity is negative
for spending. Only overspent categories are listed: use get_category_balances
for all of them, get_spending_trends to compare with earlier months, and
forecast_balance for the months ahead. One YNAB request; changes nothing.

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
| `month` | string | non | `"current"` | 'YYYY-MM-01' or 'current'. |

## Retour

| Champ | Type | Description |
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
{
  "month": "2026-09-01",
  "income": 0.0,
  "budgeted": 1967.67,
  "activity": -1206.68,
  "ready_to_assign": 1729.32,
  "age_of_money": 47,
  "overspent": [
    {
      "category_id": "cat-restaurants",
      "name": "Restaurants",
      "group": "Quotidien",
      "balance": -22.5
    }
  ]
}
```

## Erreurs

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Faire le point sur un mois](/avenir-mcp/fr/guides/monthly-review/)
