---
title: "list_accounts"
description: "List the budget's accounts with their current balances (in currency units)."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

List the budget's accounts with their current balances (in currency units).

Use it to reconcile YNAB with the bank.

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

## Retour

`array of object`

| Champ | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the account. |
| `name` | string | Account name. |
| `type` | string | YNAB account type, e.g. checking, savings, creditCard, otherAsset. |
| `on_budget` | boolean | False for a tracking account, whose transactions take no category. |
| `closed` | boolean | True when the account is closed in YNAB. |
| `balance` | number | Balance of all transactions. |
| `cleared_balance` | number | Balance of the transactions the bank has shown. |
| `uncleared_balance` | number | Balance of the transactions the bank has not shown yet. |

## Exemple

Arguments :

```json
{
  "budget_id": "demo-budget"
}
```

Réponse sur le budget de démonstration :

```json
[
  {
    "id": "acc-checking",
    "name": "Checking",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3512.66,
    "cleared_balance": 3512.66,
    "uncleared_balance": 0.0
  },
  {
    "id": "acc-savings",
    "name": "Savings",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0
  }
]
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
