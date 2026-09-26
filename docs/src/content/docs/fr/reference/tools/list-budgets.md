---
title: "list_budgets"
description: "List all YNAB budgets accessible with the current API key."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

List all YNAB budgets accessible with the current API key.

Use the budget id in subsequent tool calls. 'last-used' also works, but names
whichever budget was last opened in YNAB: with several budgets, pass the id.

## Comportement

| | |
|---|---|
| Nature | lecture seule |
| Confirmation | non |
| Annulation | non |
| Idempotent | oui |
| Requêtes YNAB | 1 pour l'exemple ci-dessous, cache vide |

## Paramètres

aucun.

## Retour

`array of object`

| Champ | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the budget, to pass as budget_id. |
| `name` | string | Budget name. |
| `first_month` | string \| null | First month with data, YYYY-MM-01; null for an empty budget. |
| `last_month` | string \| null | Last month with data, YYYY-MM-01; null for an empty budget. |

## Exemple

Arguments :

```json
{}
```

Réponse sur le budget de démonstration :

```json
[
  {
    "id": "demo-budget",
    "name": "Demo household",
    "first_month": "2026-06-01",
    "last_month": "2026-09-01"
  }
]
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
