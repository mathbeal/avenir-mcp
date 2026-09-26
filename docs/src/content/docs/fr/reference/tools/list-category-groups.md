---
title: "list_category_groups"
description: "List the category groups a new category can be created in."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

List the category groups a new category can be created in.

Hidden, deleted and system groups are left out. Pass a group id to
create_category.

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
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

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
    "id": "grp-bills",
    "name": "Bills"
  },
  {
    "id": "grp-everyday",
    "name": "Everyday"
  },
  {
    "id": "grp-fun",
    "name": "Fun"
  },
  {
    "id": "grp-savings-goals",
    "name": "Savings goals"
  }
]
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
