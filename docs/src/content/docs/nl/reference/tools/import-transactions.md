---
title: "import_transactions"
description: "Import the latest transactions from the plan's linked bank accounts into YNAB."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Import the latest transactions from the plan's linked bank accounts into YNAB.

The same as pressing Import in YNAB: nothing is deleted or changed, and YNAB never
imports a transaction twice, so it is applied at once, without a preview. Use it
before classifying or reconciling, so that the list is complete. Accounts without
a bank connection are left as they are. Imported transactions stay unapproved for
the user to review; to take one back, delete it in YNAB.

## Gedrag

| | |
|---|---|
| Soort | schrijven — verborgen zonder `AVENIR_MCP_WRITE=1` |
| Bevestiging | nee |
| Ongedaan maken | nee |
| Destructief | nee |
| Idempotent | ja |
| YNAB-verzoeken | 1 voor het voorbeeld hieronder, lege cache |

## Parameters

| Naam | Type | Verplicht | Standaard | Beschrijving |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |

## Resultaat

| Veld | Type | Beschrijving |
|---|---|---|
| `imported` | integer | Number of transactions YNAB imported from the linked accounts. |
| `transaction_ids` | array of string | Their ids, e.g. for find_transactions or approve_transactions. |
| `message` | string | What happened and what to do next, for the agent to relay. |

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
  "imported": 0,
  "transaction_ids": [],
  "message": "No new transaction to import."
}
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Zie ook

- [Openstaande transacties categoriseren](/avenir-mcp/nl/guides/classify/)
