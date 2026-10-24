---
title: "list_category_groups"
description: "List the category groups a category can be created in or moved to."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

List the category groups a category can be created in or moved to.

A group is a heading over categories: it holds no amount of its own, so nothing
here says what was budgeted or spent.
A group id goes to create_category, or to update_category as category_group_id.
For the money in each category use get_category_balances; to classify
transactions, suggest_categories. With several plans, pass the plan id from
list_plans: 'last-used' follows the plan last opened in YNAB. Hidden, deleted and
system groups are left out. One YNAB request; changes nothing.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 1 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |

## Rückgabe

`array of object`

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget"
}
```

Antwort auf dem Demo-Budget:

```json
[
  {
    "id": "grp-bills",
    "name": "Fixkosten"
  },
  {
    "id": "grp-everyday",
    "name": "Alltag"
  },
  {
    "id": "grp-fun",
    "name": "Freizeit"
  },
  {
    "id": "grp-savings-goals",
    "name": "Sparziele"
  }
]
```

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.
