---
title: "list_plans"
description: "List all YNAB plans accessible with the current API key."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

List all YNAB plans accessible with the current API key.

A plan is what YNAB now calls a budget, and what users may still call their budget.
Use the plan id in subsequent tool calls. 'last-used' also works, but names
whichever plan was last opened in YNAB: with several plans, pass the id.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 1 für das Beispiel unten, leerer Cache |

## Parameter

keine.

## Rückgabe

`array of object`

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | string | YNAB id of the plan, to pass as plan_id. |
| `name` | string | Plan name. |
| `first_month` | string \| null | First month with data, YYYY-MM-01; null for an empty plan. |
| `last_month` | string \| null | Last month with data, YYYY-MM-01; null for an empty plan. |

## Beispiel

Argumente:

```json
{}
```

Antwort auf dem Demo-Budget:

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

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.
