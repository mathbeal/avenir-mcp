---
title: "forecast_balance"
description: "Project the balance month by month and say when money would run out."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Project the balance month by month and say when money would run out.

Starts from today's balance of the open on-budget accounts (or those given).
For the current month, what was already spent or received since the 1st is
deducted from the monthly averages, so only what is left is projected.
Assumes, and returns as `assumptions` so the user can correct them:
charges that recur in the last 4 months (same payee, stable amount), the
average of all other spending over the last 3 months, and what you pass:
expected monthly income (default: the last 3 months' non-recurring inflows,
which may include one-off money such as capital injections) and one-off amounts
such as a tax bill (negative) or a refund (positive). Amounts in currency
units. `lowest` is the lowest point within a month; `first_shortfall` is the
first month it goes below zero. Changes nothing.

## Comportement

| | |
|---|---|
| Nature | lecture seule |
| Confirmation | non |
| Annulation | non |
| Idempotent | oui |
| Requêtes YNAB | 2 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `plan_id` | string | oui | — | YNAB plan id or 'last-used'. |
| `until` | string | oui | — | Last month to project, YYYY-MM, at most 24 months ahead. |
| `account_ids` | array of string \| null | non | `null` | Accounts to include (from list_accounts); default all open on-budget accounts. |
| `monthly_income` | number \| null | non | `null` | Income expected each month, replacing the income found in the history (recurring or average); default: what the history shows. |
| `variable_monthly` | number \| null | non | `null` | Monthly spending besides recurring charges (negative); default: the last 3 months' average. |
| `one_offs` | array of object \| null | non | `null` | Expected one-off amounts: {date YYYY-MM-DD, amount, label}. |

## Retour

| Champ | Type | Description |
|---|---|---|
| `message` | string | The conclusion in one sentence, for the agent to relay. |
| `accounts` | array of string | Names of the accounts projected together. |
| `start_balance` | number | Their total balance today. |
| `assumptions` | object | Everything the projection assumed, to check with the user. |
| `assumptions.recurring` | array of object | Charges and income found recurring in the history. |
| `assumptions.variable_monthly` | number | Monthly spending besides recurring charges, negative. |
| `assumptions.monthly_income` | number | Monthly income assumed, besides recurring income. |
| `assumptions.one_offs` | array of object | One-off amounts given by the caller. |
| `months` | array of object | The projected months. |
| `months[].month` | string | Month, YYYY-MM. |
| `months[].start` | number | Projected balance on the first day (today's balance for the current month). |
| `months[].inflows` | number | Money expected in during the month. |
| `months[].outflows` | number | Money expected out during the month, negative. |
| `months[].end` | number | Projected balance at the end of the month. |
| `months[].lowest` | number | Lowest projected balance within the month, day by day. |
| `first_shortfall` | string \| null | First month whose lowest balance is below zero; null if none. |

## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget",
  "until": "2026-12",
  "monthly_income": 3200
}
```

Réponse sur le budget de démonstration :

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
        "payee": "LANDLORD SARL",
        "amount": -950.0,
        "day": 3,
        "months_seen": 3
      },
      {
        "payee": "MARKET FRESH",
        "amount": -182.58,
        "day": 14,
        "months_seen": 3
      },
      {
        "payee": "POWERCO ENERGIE",
        "amount": -64.2,
        "day": 12,
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
        "payee": "TELCO MOBILE - PRELEV",
        "amount": -19.99,
        "day": 8,
        "months_seen": 3
      },
      "… 1 more"
    ],
    "variable_monthly": -68.7,
    "monthly_income": 3200.0,
    "one_offs": []
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
      "outflows": -1365.96,
      "end": 9146.7,
      "lowest": 6665.72
    },
    {
      "month": "2026-11",
      "start": 9146.7,
      "inflows": 3200.0,
      "outflows": -1365.96,
      "end": 10980.74,
      "lowest": 8509.84
    },
    {
      "month": "2026-12",
      "start": 10980.74,
      "inflows": 3200.0,
      "outflows": -1365.96,
      "end": 12814.78,
      "lowest": 10333.8
    }
  ],
  "first_shortfall": null
}
```

## Erreurs

- `Unknown account(s) {unknown}: use ids from list_accounts.`
- `until must be the current month or later.`
- `until must be at most 24 months ahead.`
- `until must be a month as YYYY-MM, got '{until}'.`

Les erreurs propres à YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Anticiper](/avenir-mcp/fr/guides/plan-ahead/)
