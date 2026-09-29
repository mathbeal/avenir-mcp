---
title: "list_accounts"
description: "List the plan's accounts with their current balances (in currency units)."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

List the plan's accounts with their current balances (in currency units).

Use it to reconcile YNAB with the bank.

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
| `id` | string | YNAB id of the account. |
| `name` | string | Account name. |
| `type` | string | YNAB account type, e.g. checking, savings, creditCard, otherAsset. |
| `on_budget` | boolean | False for a tracking account, whose transactions take no category. |
| `closed` | boolean | True when the account is closed in YNAB. |
| `balance` | number | Balance of all transactions. |
| `cleared_balance` | number | Balance of the transactions the bank has shown. |
| `uncleared_balance` | number | Balance of the transactions the bank has not shown yet. |

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
    "id": "acc-checking",
    "name": "Checking",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3512.66,
    "cleared_balance": 3512.66,
    "uncleared_balance": 0.0
  },
  {
    "id": "acc-savings",
    "name": "Savings",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0
  }
]
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.
