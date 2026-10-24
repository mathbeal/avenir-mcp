---
title: "list_category_groups"
description: "List the category groups a category can be created in or moved to."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

List the category groups a category can be created in or moved to.

A group is a heading over categories: it holds no amount of its own, so nothing
here says what was budgeted or spent.
A group id goes to create_category, or to update_category as category_group_id.
For the money in each category use get_category_balances; to classify
transactions, suggest_categories. With several plans, pass the plan id from
list_plans: 'last-used' follows the plan last opened in YNAB. Hidden, deleted and
system groups are left out. One YNAB request; changes nothing.

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
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

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
    "id": "grp-bills",
    "name": "Charges fixes"
  },
  {
    "id": "grp-everyday",
    "name": "Quotidien"
  },
  {
    "id": "grp-fun",
    "name": "Loisirs"
  },
  {
    "id": "grp-savings-goals",
    "name": "Projets"
  }
]
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.
