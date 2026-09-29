---
title: "import_transactions"
description: "Import the latest transactions from the plan's linked bank accounts into YNAB."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Import the latest transactions from the plan's linked bank accounts into YNAB.

The same as pressing Import in YNAB: nothing is deleted or changed, and YNAB never
imports a transaction twice, so it is applied at once, without a preview. Use it
before classifying or reconciling, so that the list is complete. Accounts without
a bank connection are left as they are. Imported transactions stay unapproved for
the user to review; to take one back, delete it in YNAB.

## Comportement

| | |
|---|---|
| Nature | écriture — masqué sans `AVENIR_MCP_WRITE=1` |
| Confirmation | non |
| Annulation | non |
| Destructif | non |
| Idempotent | oui |
| Requêtes YNAB | 1 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `plan_id` | string | oui | — | YNAB plan id or 'last-used'. |

## Retour

| Champ | Type | Description |
|---|---|---|
| `imported` | integer | Number of transactions YNAB imported from the linked accounts. |
| `transaction_ids` | array of string | Their ids, e.g. for find_transactions or approve_transactions. |
| `message` | string | What happened and what to do next, for the agent to relay. |

## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget"
}
```

Réponse sur le budget de démonstration :

```json
{
  "imported": 0,
  "transaction_ids": [],
  "message": "No new transaction to import."
}
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Classer les transactions en attente](/avenir-mcp/fr/guides/classify/)
