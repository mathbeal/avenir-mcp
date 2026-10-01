---
title: "list_accounts"
description: "List the plan's accounts with their balances, bank link and last reconciliation."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

List the plan's accounts with their balances, bank link and last reconciliation.

Use it to reconcile YNAB with the bank, and to tell the user when a bank link is
broken (no transaction comes in until they fix it in YNAB) or when an account has
not been reconciled for months. Its ids are the account_ids other tools take.
Balances are in currency units. Every account comes in one response, closed
ones included, in one YNAB request; changes nothing.

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
| `bank_link` | "healthy" \| "broken" \| "none" | Whether YNAB imports this account from the bank: broken means the connection needs the user's attention in YNAB, and no new transaction will come in until then. |
| `last_reconciled` | string \| null | Date (YYYY-MM-DD) of the last reconciliation, or None if never reconciled. |

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
    "name": "Betaalrekening",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3328.5,
    "cleared_balance": 3328.5,
    "uncleared_balance": 0.0,
    "bank_link": "healthy",
    "last_reconciled": "2026-08-31"
  },
  {
    "id": "acc-savings",
    "name": "Spaarrekening",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  {
    "id": "acc-joint-savings",
    "name": "Gezamenlijke spaarrekening",
    "type": "savings",
    "on_budget": false,
    "closed": false,
    "balance": 16342.36,
    "cleared_balance": 16342.36,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  {
    "id": "acc-car-loan",
    "name": "Autolening",
    "type": "autoLoan",
    "on_budget": false,
    "closed": false,
    "balance": -19040.81,
    "cleared_balance": -19040.81,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  "… 2 more"
]
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.
