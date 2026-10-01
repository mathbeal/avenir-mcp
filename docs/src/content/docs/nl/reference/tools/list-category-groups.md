---
title: "list_category_groups"
description: "List the category groups a new category can be created in."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

List the category groups a new category can be created in.

Hidden, deleted and system groups are left out. Pass a group id to
create_category, which is there only when the operator enabled writes.

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
