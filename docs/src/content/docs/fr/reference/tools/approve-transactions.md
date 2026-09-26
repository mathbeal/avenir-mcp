---
title: "approve_transactions"
description: "Mark transactions as approved, i.e. reviewed (clears YNAB's \"unapproved\" badge)."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

Only approve transactions whose category has been checked.

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
| `budget_id` | string | oui | — | YNAB budget UUID or 'last-used'. |
| `tx_ids` | array of string | oui | — | Transaction UUIDs to approve. |

## Retour

| Champ | Type | Description |
|---|---|---|
| `approved` | integer | Number of transactions YNAB updated. |

## Exemple

Arguments :

```json
{
  "budget_id": "demo-budget",
  "tx_ids": [
    "tx-048",
    "tx-049"
  ]
}
```

Réponse sur le budget de démonstration :

```json
{
  "approved": 2
}
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
