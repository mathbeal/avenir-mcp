---
title: "list_plans"
description: "List all YNAB plans accessible with the current API key."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

List all YNAB plans accessible with the current API key.

A plan is what YNAB now calls a budget, and what users may still call their budget.
Use the plan id in subsequent tool calls. 'last-used' also works, but names
whichever plan was last opened in YNAB: with several plans, pass the id.

## Gedrag

| | |
|---|---|
| Soort | alleen lezen |
| Bevestiging | nee |
| Ongedaan maken | nee |
| Idempotent | ja |
| YNAB-verzoeken | 1 voor het voorbeeld hieronder, lege cache |

## Parameters

geen.

## Resultaat

`array of object`

| Veld | Type | Beschrijving |
|---|---|---|
| `id` | string | YNAB id of the budget, to pass as plan_id. |
| `name` | string | Budget name. |
| `first_month` | string \| null | First month with data, YYYY-MM-01; null for an empty budget. |
| `last_month` | string \| null | Last month with data, YYYY-MM-01; null for an empty budget. |

## Voorbeeld

Argumenten:

```json
{}
```

Antwoord op het demobudget:

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

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.
