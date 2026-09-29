---
title: "approve_transactions"
description: "Mark transactions as approved, i.e. reviewed (clears YNAB's \"unapproved\" badge)."
---

:::note[Gegenereerd]
Gegenereerd uit de code door `python -m docsgen`; een test faalt zodra de pagina niet meer overeenkomt. De beschrijvingen komen uit de code en blijven in het Engels: de taal waarin agents ze lezen.
:::

## Doel

Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

Only approve transactions whose category has been checked.

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
| `tx_ids` | array of string | ja | — | Transaction UUIDs to approve. |

## Resultaat

| Veld | Type | Beschrijving |
|---|---|---|
| `approved` | integer | Number of transactions YNAB updated. |

## Voorbeeld

Argumenten:

```json
{
  "plan_id": "demo-budget",
  "tx_ids": [
    "tx-048",
    "tx-049"
  ]
}
```

Antwoord op het demobudget:

```json
{
  "approved": 2
}
```

## Fouten

Deze tool geeft zelf geen fouten; fouten van YNAB komen terug als `Error calling tool '<tool>': YNAB <status>: <detail>`.
