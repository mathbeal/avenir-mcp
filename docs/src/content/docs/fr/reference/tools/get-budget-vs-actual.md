---
title: "get_budget_vs_actual"
description: "Return a budget-vs-actual breakdown with utilisation percentage per category."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Return a budget-vs-actual breakdown with utilisation percentage per category.

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
| `budget_id` | string | oui | — | YNAB budget UUID or 'last-used'. |
| `month` | string | non | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Retour

`array of object`


## Exemple

Arguments :

```json
{
  "budget_id": "demo-budget",
  "month": "2026-09-01"
}
```

Réponse sur le budget de démonstration :

```json
[
  {
    "id": "cat-rent",
    "name": "Rent",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Electricity",
    "budgeted": 70.0,
    "actual": 0.0,
    "balance": 70.0,
    "utilization_pct": 0.0
  },
  {
    "id": "cat-phone",
    "name": "Phone",
    "budgeted": 20.0,
    "actual": 19.99,
    "balance": 0.01,
    "utilization_pct": 99.9
  },
  {
    "id": "cat-groceries",
    "name": "Groceries",
    "budgeted": 400.0,
    "actual": 0.0,
    "balance": 400.0,
    "utilization_pct": 0.0
  },
  "… 5 more"
]
```

## Erreurs

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Faire le point sur un mois](/avenir-mcp/fr/guides/monthly-review/)
