---
title: "list_accounts"
description: "List the plan's accounts with their balances, bank link and last reconciliation."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

List the plan's accounts with their balances, bank link and last reconciliation.

Use it to reconcile YNAB with the bank, and to tell the user when a bank link is
broken (no transaction comes in until they fix it in YNAB) or when an account has
not been reconciled for months. Balances are in currency units.

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
| `bank_link` | "healthy" \| "broken" \| "none" | Whether YNAB imports this account from the bank: broken means the connection needs the user's attention in YNAB, and no new transaction will come in until then. |
| `last_reconciled` | string \| null | Date (YYYY-MM-DD) of the last reconciliation, or None if never reconciled. |

## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget"
}
```

Réponse sur le budget de démonstration :

```json
[
  {
    "id": "acc-checking",
    "name": "Compte courant",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3328.5,
    "cleared_balance": 3328.5,
    "uncleared_balance": 0.0,
    "bank_link": "healthy",
    "last_reconciled": "2026-08-31"
  },
  {
    "id": "acc-savings",
    "name": "Épargne",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  }
]
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
