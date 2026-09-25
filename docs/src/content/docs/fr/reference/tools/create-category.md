---
title: "create_category"
description: "Create a category in a group, after the user confirms."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Create a category in a group, after the user confirms.

YNAB's API cannot delete a category: to undo, hide it in YNAB. A name already
used in the group is refused. Confirmation works as for apply_categories.

## Comportement

| | |
|---|---|
| Nature | écriture — masqué sans `AVENIR_MCP_WRITE=1` |
| Confirmation | oui : aperçu, puis application après accord de l'utilisateur |
| Annulation | non |
| Destructif | non |
| Idempotent | non |
| Requêtes YNAB | 2 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `budget_id` | string | oui | — | YNAB budget UUID or 'last-used'. |
| `category_group_id` | string | oui | — | Group to create it in (from list_category_groups). |
| `name` | string | oui | — | Name of the new category. |
| `confirmation` | string \| null | non | `null` | Code from a previous "confirmation_required" result. |

## Retour

| Champ | Type | Description |
|---|---|---|
| `status` | "applied" \| "confirmation_required" \| "declined" \| "nothing_to_do" | Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the user agrees), declined (the user said no), or nothing_to_do. |
| `message` | string | What happened and what to do next, for the agent to relay. |
| `name` | string | Name of the new category, trimmed. |
| `group` | string | Group it goes in. |
| `category_id` | string \| null | YNAB id of the new category; null until applied. |
| `confirmation` | string \| null | Single-use code confirming exactly this preview, valid 10 minutes; null unless status is confirmation_required. |

## Exemple

Arguments :

```json
{
  "budget_id": "demo-budget",
  "category_group_id": "grp-everyday",
  "name": "Pets"
}
```

Réponse sur le budget de démonstration :

```json
{
  "status": "confirmation_required",
  "message": "Nothing changed yet. Create category 'Pets' in Everyday? If the user agrees, call again with this code.",
  "name": "Pets",
  "group": "Everyday",
  "category_id": null,
  "confirmation": "<confirmation code>"
}
```

## Erreurs

- `Group {category_group_id} is not in this budget: use an id from list_category_groups.`
- `The name is empty: give the new category a name.`
- `'{new_name}' already exists in {group}.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Organiser les catégories](/avenir-mcp/fr/guides/categories/)
