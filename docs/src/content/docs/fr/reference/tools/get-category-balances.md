---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Budgeted, spent (activity) and available (balance) per category for a month.

Use it for "how much is left in Groceries?" or to list every category's money.
Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. For the share of
each budget consumed use get_budget_vs_actual; for the month's totals,
get_monthly_summary. One YNAB request; changes nothing.

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
| `include_empty` | boolean | non | `false` | Also list categories with no amount at all. |

## Retour

`array of object`

| Champ | Type | Description |
|---|---|---|
| `category_id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group. |
| `budgeted` | number | Amount assigned to the category this month. |
| `activity` | number | Amount spent (negative) or received in the category this month. |
| `balance` | number | Available at the end of the month: carried over, plus budgeted, plus activity. |

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
    "category_id": "cat-rent",
    "name": "Loyer",
    "group": "Charges fixes",
    "budgeted": 950.0,
    "activity": -950.0,
    "balance": 0.0
  },
  {
    "category_id": "cat-power",
    "name": "Électricité",
    "group": "Charges fixes",
    "budgeted": 64.2,
    "activity": -64.2,
    "balance": 0.0
  },
  {
    "category_id": "cat-internet",
    "name": "Box internet",
    "group": "Charges fixes",
    "budgeted": 29.99,
    "activity": -29.99,
    "balance": 0.0
  },
  {
    "category_id": "cat-phone",
    "name": "Téléphone",
    "group": "Charges fixes",
    "budgeted": 19.99,
    "activity": -19.99,
    "balance": 0.0
  },
  "… 6 more"
]
```

## Erreurs

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Faire le point sur un mois](/avenir-mcp/fr/guides/monthly-review/)
