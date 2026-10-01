---
title: "get_spending_trends"
description: "Spending per category, month by month, over the last N months."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Spending per category, month by month, over the last N months.

Use it for "is my grocery spending going up?" or to compare months. The result
maps each category name to its spending month by month, oldest first, as a
positive number in currency units. For a single month use get_category_balances
or get_budget_vs_actual; for the months ahead, forecast_balance. One YNAB
request for the list of months, then one per month; changes nothing.

## Gedrag

| | |
|---|---|
| Soort | alleen lezen |
| Bevestiging | nee |
| Ongedaan maken | nee |
| Idempotent | ja |
| YNAB-verzoeken | 4 voor het voorbeeld hieronder, lege cache |

## Parameters

| Naam | Type | Verplicht | Standaard | Beschrijving |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | nee | `3` | Number of past months to include, 1 to 24 (default 3). |

## Resultaat

`object`


## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget",
  "months_count": 3
}
```

Antwoord op het demobudget:

```json
{
  "Huur": [
    {
      "month": "2026-07-01",
      "amount": 950.0
    },
    {
      "month": "2026-08-01",
      "amount": 950.0
    },
    {
      "month": "2026-09-01",
      "amount": 950.0
    }
  ],
  "Stroom": [
    {
      "month": "2026-07-01",
      "amount": 64.2
    },
    {
      "month": "2026-08-01",
      "amount": 64.2
    },
    {
      "month": "2026-09-01",
      "amount": 64.2
    }
  ],
  "Internet": [
    {
      "month": "2026-07-01",
      "amount": 29.99
    },
    {
      "month": "2026-08-01",
      "amount": 29.99
    },
    {
      "month": "2026-09-01",
      "amount": 29.99
    }
  ],
  "Telefoon": [
    {
      "month": "2026-07-01",
      "amount": 19.99
    },
    {
      "month": "2026-08-01",
      "amount": 19.99
    },
    {
      "month": "2026-09-01",
      "amount": 19.99
    }
  ],
  "Boodschappen": [
    {
      "month": "2026-07-01",
      "amount": 172.89
    },
    {
      "month": "2026-08-01",
      "amount": 192.51
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Restaurants": [
    {
      "month": "2026-07-01",
      "amount": 61.5
    },
    {
      "month": "2026-08-01",
      "amount": 89.1
    },
    {
      "month": "2026-09-01",
      "amount": 142.5
    }
  ],
  "Vervoer": [
    {
      "month": "2026-07-01",
      "amount": 45.0
    },
    {
      "month": "2026-08-01",
      "amount": 45.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Tennis": [
    {
      "month": "2026-07-01",
      "amount": 22.0
    },
    {
      "month": "2026-08-01",
      "amount": 22.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Abonnementen": [
    {
      "month": "2026-07-01",
      "amount": 13.49
    },
    {
      "month": "2026-08-01",
      "amount": 13.49
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Vakantie": [
    {
      "month": "2026-07-01",
      "amount": 0.0
    },
    {
      "month": "2026-08-01",
      "amount": 0.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ]
}
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Een maand doornemen](/avenir-mcp/nl/guides/monthly-review/)
