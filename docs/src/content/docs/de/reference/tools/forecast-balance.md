---
title: "forecast_balance"
description: "Project the balance month by month and say when money would run out."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Project the balance month by month and say when money would run out.

Starts from today's balance of the open on-budget accounts (or those given).
For the current month, what was already spent or received since the 1st is
deducted from the monthly averages, so only what is left is projected.
Assumes, and returns as `assumptions` so the user can correct them:
YNAB's scheduled transactions on their dates (a payee with a schedule is
projected by it alone; transfers between projected accounts left out),
charges that recur in the last 4 months (same payee, stable amount), the
average of all other spending over the last 3 months, and what you pass:
expected monthly income (default: the last 3 months' non-recurring inflows,
which may include one-off money such as capital injections) and one-off amounts
such as a tax bill (negative) or a refund (positive). Amounts in currency
units. `lowest` is the lowest point within a month; `first_shortfall` is the
first month it goes below zero. Changes nothing.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 4 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |
| `until` | string | ja | — | Last month to project, YYYY-MM, at most 24 months ahead. |
| `account_ids` | array of string \| null | nein | `null` | Accounts to include (from list_accounts); default all open on-budget accounts. |
| `monthly_income` | number \| null | nein | `null` | Income expected each month, replacing the income found in the history (recurring or average) and scheduled in YNAB; default: what they show. |
| `variable_monthly` | number \| null | nein | `null` | Monthly spending besides recurring charges (negative); default: the last 3 months' average. |
| `one_offs` | array of object \| null | nein | `null` | Expected one-off amounts: {date YYYY-MM-DD, amount, label}; not those already scheduled in YNAB, which are counted. |

## Rückgabe

| Feld | Typ | Beschreibung |
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

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget",
  "until": "2026-12",
  "monthly_income": 3200
}
```

Antwort auf dem Demo-Budget:

```json
{
  "message": "The balance stays above zero until 2026-12. This rests on the assumptions listed: check them with the user.",
  "accounts": [
    "Checking",
    "Savings"
  ],
  "start_balance": 4112.66,
  "assumptions": {
    "recurring": [
      {
        "payee": "MARKET FRESH",
        "amount": -182.58,
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
        "payee": "TENNIS CLUB - PRELEV",
        "amount": -22.0,
        "day": 20,
        "months_seen": 3
      }
    ],
    "variable_monthly": -68.7,
    "monthly_income": 3200.0,
    "one_offs": [],
    "scheduled": [
      {
        "scheduled_id": "sch-rent",
        "date": "2026-10-03",
        "amount": -950.0,
        "account": "Checking",
        "category": "Rent",
        "payee": "LANDLORD SARL",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-phone",
        "date": "2026-10-08",
        "amount": -19.99,
        "account": "Checking",
        "category": "Phone",
        "payee": "TELCO MOBILE - PRELEV",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-power",
        "date": "2026-10-12",
        "amount": -64.2,
        "account": "Checking",
        "category": "Electricity",
        "payee": "POWERCO ENERGIE",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-insurance",
        "date": "2026-10-20",
        "amount": -420.0,
        "account": "Checking",
        "category": null,
        "payee": "HOMESAFE INSURANCE",
        "memo": null,
        "frequency": "yearly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-rent",
        "date": "2026-11-03",
        "amount": -950.0,
        "account": "Checking",
        "category": "Rent",
        "payee": "LANDLORD SARL",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      {
        "scheduled_id": "sch-phone",
        "date": "2026-11-08",
        "amount": -19.99,
        "account": "Checking",
        "category": "Phone",
        "payee": "TELCO MOBILE - PRELEV",
        "memo": null,
        "frequency": "monthly",
        "transfer": false
      },
      "… 4 more"
    ]
  },
  "months": [
    {
      "month": "2026-09",
      "start": 4112.66,
      "inflows": 3200.0,
      "outflows": 0.0,
      "end": 7312.66,
      "lowest": 4112.66
    },
    {
      "month": "2026-10",
      "start": 7312.66,
      "inflows": 3200.0,
      "outflows": -1785.96,
      "end": 8726.7,
      "lowest": 6665.72
    },
    {
      "month": "2026-11",
      "start": 8726.7,
      "inflows": 3200.0,
      "outflows": -1365.96,
      "end": 10560.74,
      "lowest": 8089.84
    },
    {
      "month": "2026-12",
      "start": 10560.74,
      "inflows": 3200.0,
      "outflows": -1365.96,
      "end": 12394.78,
      "lowest": 9913.8
    }
  ],
  "first_shortfall": null
}
```

## Fehler

- `Unknown account(s) {unknown}: use ids from list_accounts.`
- `until must be the current month or later.`
- `until must be at most 24 months ahead.`
- `until must be a month as YYYY-MM, got '{until}'.`

Fehler von YNAB selbst kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Vorausplanen](/avenir-mcp/de/guides/plan-ahead/)
