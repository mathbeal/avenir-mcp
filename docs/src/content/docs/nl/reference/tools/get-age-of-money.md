---
title: "get_age_of_money"
description: "YNAB's Age of Money: how old the money spent is today, and its trend month by month."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

YNAB's Age of Money: how old the money spent is today, and its trend month by month.

Use it for "how old is my money?", "am I living on last month's income?" or "is my
buffer growing?". The figure is YNAB's own, in days: how long, on average, money
stayed in the budget accounts before being spent, the oldest money spent first. Over
30 days means living on last month's income. The answer gives each month's figure up
to the current one, the latest, the change and its direction over the period; a month
is null when YNAB had not enough history. Relay the notes with the figures. For how
long the money would last without income use get_runway. One YNAB request, the list
of months; changes nothing.

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
| `months_count` | integer | nee | `12` | Months to show, the current one included, 1 to 24 (default 12). |

## Resultaat

| Veld | Type | Beschrijving |
|---|---|---|
| `message` | string | The conclusion in one sentence or two, for the agent to relay. |
| `days` | integer \| null | The latest Age of Money, in days; null when YNAB gives none. |
| `as_of` | string \| null | The month of that figure, YYYY-MM: the current one unless YNAB has none for it. |
| `months` | array of object | The months up to the current one, oldest first. |
| `months[].month` | string | The month, YYYY-MM. |
| `months[].days` | integer \| null | The age of the money spent, in days; null when YNAB had not enough history. |
| `months[].change` | integer \| null | Days gained (positive) or lost since the month before; null when either is unknown. |
| `change` | integer \| null | Days gained (positive) or lost from the first month with a figure to the latest; null with fewer than two figures. |
| `trend` | "up" \| "down" \| "steady" \| null | The direction of that change; null with fewer than two figures. |
| `notes` | array of string | How YNAB counts, and what is missing, to tell the user. |

## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget"
}
```

Antwoord op het demobudget:

```json
{
  "message": "Your money is 47 days old (2026-09, YNAB's Age of Money): what you spend came in 47 days before, on average. Over 30 days: you are living on last month's income, the buffer YNAB aims for. It went up by 30 days since 2026-07.",
  "days": 47,
  "as_of": "2026-09",
  "months": [
    {
      "month": "2026-06",
      "days": null,
      "change": null
    },
    {
      "month": "2026-07",
      "days": 17,
      "change": null
    },
    {
      "month": "2026-08",
      "days": 48,
      "change": 31
    },
    {
      "month": "2026-09",
      "days": 47,
      "change": -1
    }
  ],
  "change": 30,
  "trend": "up",
  "notes": [
    "Age of Money is YNAB's own figure: for the latest payments out of the budget accounts, how many days passed since that money came in, the oldest money spent first, averaged.",
    "The current month's figure moves with each payment; a past month's is the one YNAB keeps for it.",
    "No figure for 2026-06: YNAB did not have enough history of money in and out yet.",
    "YNAB holds only 4 months up to 2026-09: all are shown."
  ]
}
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Een maand doornemen](/avenir-mcp/nl/guides/monthly-review/)
