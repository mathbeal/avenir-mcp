---
title: "forecast_balance"
description: "Project the balance month by month and say when money would run out."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Project the balance month by month and say when money would run out.

Starts from today's balance of the open on-budget accounts (or those given).
For the current month, what was already spent or received since the 1st is
deducted from the monthly averages, so only what is left is projected.
Assumes, and returns as `assumptions` so the user can correct them: YNAB's
scheduled transactions on their dates, whatever their frequency, a yearly bill
included, charges that recur in the last 4 months (same payee, stable amount),
the average of all other spending over the last 3 months, and what you pass.
A payee with a schedule is projected by that schedule alone, and transfers
between the projected accounts are left out. What you pass is the expected
monthly income (default: the last 3 months' non-recurring inflows, which may
include one-off money such as capital injections) and one-off amounts such as
a tax bill (negative) or a refund (positive). Amounts in currency units.
`lowest` is the lowest point within a month; `first_shortfall` is the first
month it goes below zero. For a month already gone use get_monthly_summary, or
get_spending_trends to compare several; for how long today's money would last
with no income at all, get_runway. Changes nothing.

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
| `until` | string | ja | — | Last month to project, YYYY-MM, at most 24 months ahead. |
| `account_ids` | array of string \| null | nee | `null` | Accounts to include (from list_accounts); default all open on-budget accounts. |
| `monthly_income` | number \| null | nee | `null` | Income expected each month, replacing the income found in the history (recurring or average) and scheduled in YNAB; default: what they show. |
| `variable_monthly` | number \| null | nee | `null` | Monthly spending besides recurring charges (negative); default: the last 3 months' average. |
| `one_offs` | array of object \| null | nee | `null` | Expected one-off amounts: {date YYYY-MM-DD, amount, label}; not those already scheduled in YNAB, which are counted. |

## Resultaat

| Veld | Type | Beschrijving |
|---|---|---|
| `message` | string | The conclusion in one sentence, for the agent to relay. |
| `accounts` | array of string | Names of the accounts projected together. |
| `start_balance` | number | Their total balance today. |
| `assumptions` | object | Everything the projection assumed, to check with the user. |
| `assumptions.recurring` | array of object | Charges and income found recurring in the history. |
| `assumptions.variable_monthly` | number | Monthly spending besides recurring charges, negative. |
| `assumptions.monthly_income` | number | Monthly income assumed, besides recurring income. |
| `assumptions.one_offs` | array of object | One-off amounts given by the caller. |
| `assumptions.scheduled` | array of object | Scheduled transactions of the projected accounts, from tomorrow to the last month; they replace what the history suggests for the same payees. Transfers between the projected accounts are left out. |
| `months` | array of object | The projected months. |
| `months[].month` | string | Month, YYYY-MM. |
| `months[].start` | number | Projected balance on the first day (today's balance for the current month). |
| `months[].inflows` | number | Money expected in during the month. |
| `months[].outflows` | number | Money expected out during the month, negative. |
| `months[].end` | number | Projected balance at the end of the month. |
| `months[].lowest` | number | Lowest projected balance within the month, day by day. |
| `first_shortfall` | string \| null | First month whose lowest balance is below zero; null if none. |

## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget",
  "until": "2026-12",
  "monthly_income": 3200
}
```

Antwoord op het demobudget:

```json
{
  "message": "The balance stays above zero until 2026-12. This rests on the assumptions listed: check them with the user.",
  "accounts": [
    "Betaalrekening",
    "Spaarrekening"
  ],
  "start_balance": 3134.48,
  "assumptions": {
    "recurring": [
      {
        "payee": "CHEZ LUCIE",
        "amount": -49.2,
        "day": 10,
        "months_seen": 3
      },
      {
        "payee": "MARKET FRESH",
        "amount": -395.9,
        "day": 14,
        "months_seen": 3
      },
      {
        "payee": "RAIL CO",
        "amount": -45.0,
        "day": 18,
        "months_seen": 3
      },
      {
        "payee": "STREAMFLIX",
        "amount": -13.49,
        "day": 15,
        "months_seen": 3
      },
      {
        "payee": "SUSHI GO",
        "amount": -64.5,
        "day": 24,
        "months_seen": 3
      },
      {
        "payee": "TENNIS CLUB - PRELEV",
        "amount": -22.0,
        "day": 20,
        "months_seen": 3
      }
    ],
    "variable_monthly": 0.0,
    "monthly_income": 3200.0,
    "one_offs": [],
    "scheduled": [
      {
        "scheduled_id": "sch-rent",
        "date": "2026-10-03",
        "amount": -950.0,
        "account": "Betaalrekening",
        "category": "Huur",
        "payee": "LANDLORD SARL",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-internet",
        "date": "2026-10-06",
        "amount": -29.99,
        "account": "Betaalrekening",
        "category": "Internet",
        "payee": "FIBERNET - PRELEV",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-phone",
        "date": "2026-10-08",
        "amount": -19.99,
        "account": "Betaalrekening",
        "category": "Telefoon",
        "payee": "TELCO MOBILE - PRELEV",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-power",
        "date": "2026-10-12",
        "amount": -64.2,
        "account": "Betaalrekening",
        "category": "Stroom",
        "payee": "POWERCO ENERGIE",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-insurance",
        "date": "2026-10-20",
        "amount": -420.0,
        "account": "Betaalrekening",
        "category": "Woningverzekering",
        "payee": "HOMESAFE INSURANCE",
        "memo": null,
        "frequency": "yearly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-rent",
        "date": "2026-11-03",
        "amount": -950.0,
        "account": "Betaalrekening",
        "category": "Huur",
        "payee": "LANDLORD SARL",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      "… 7 more"
    ]
  },
  "months": [
    {
      "month": "2026-09",
      "start": 3134.48,
      "inflows": 3200.0,
      "outflows": 0.0,
      "end": 6334.48,
      "lowest": 3134.48
    },
    {
      "month": "2026-10",
      "start": 6334.48,
      "inflows": 3200.0,
      "outflows": -2074.27,
      "end": 7460.21,
      "lowest": 5694.17
    },
    {
      "month": "2026-11",
      "start": 7460.21,
      "inflows": 3200.0,
      "outflows": -1654.27,
      "end": 9005.94,
      "lowest": 6830.22
    },
    {
      "month": "2026-12",
      "start": 9005.94,
      "inflows": 3200.0,
      "outflows": -1654.27,
      "end": 10551.67,
      "lowest": 8365.63
    }
  ],
  "first_shortfall": null
}
```

## Fouten

- `Unknown account(s) {unknown}: use ids from list_accounts.`
- `until must be the current month or later.`
- `until must be at most 24 months ahead.`
- `until must be a month as YYYY-MM, got '{until}'.`

Fouten van YNAB zelf komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Vooruit plannen](/avenir-mcp/nl/guides/plan-ahead/)
