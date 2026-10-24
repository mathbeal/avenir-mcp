---
title: "list_category_groups"
description: "List the category groups a category can be created in or moved to."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

List the category groups a category can be created in or moved to.

A group is a heading over categories: it holds no amount of its own, so nothing
here says what was budgeted or spent.
A group id goes to create_category, or to update_category as category_group_id.
For the money in each category use get_category_balances; to classify
transactions, suggest_categories. With several plans, pass the plan id from
list_plans: 'last-used' follows the plan last opened in YNAB. Hidden, deleted and
system groups are left out. One YNAB request; changes nothing.

## Gedrag

| | |
|---|---|
| Soort | alleen lezen |
| Bevestiging | nee |
| Ongedaan maken | nee |
| Idempotent | ja |
| YNAB-verzoeken | 1 voor het voorbeeld hieronder, lege cache |

## Parameters

| Naam | Type | Verplicht | Standaard | Beschrijving |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |

## Resultaat

`array of object`

| Veld | Type | Beschrijving |
|---|---|---|
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget"
}
```

Antwoord op het demobudget:

```json
[
  {
    "id": "grp-bills",
    "name": "Vaste lasten"
  },
  {
    "id": "grp-everyday",
    "name": "Dagelijks"
  },
  {
    "id": "grp-fun",
    "name": "Vrije tijd"
  },
  {
    "id": "grp-savings-goals",
    "name": "Spaardoelen"
  }
]
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.
