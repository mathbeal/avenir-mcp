---
title: "import_transactions"
description: "Import the latest transactions from the plan's linked bank accounts into YNAB."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Import the latest transactions from the plan's linked bank accounts into YNAB.

The same as pressing Import in YNAB: nothing is deleted or changed, and YNAB never
imports a transaction twice, so it is applied at once, without a preview. Use it
before classifying or reconciling, so that the list is complete. Accounts without
a bank connection are left as they are. Imported transactions stay unapproved for
the user to review; to take one back, delete it in YNAB.

## Verhalten

| | |
|---|---|
| Art | schreibend — ohne `AVENIR_MCP_WRITE=1` verborgen |
| Bestätigung | nein |
| Rückgängig | nein |
| Destruktiv | nein |
| Idempotent | ja |
| YNAB-Anfragen | 1 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |

## Rückgabe

| Feld | Typ | Beschreibung |
|---|---|---|
| `imported` | integer | Number of transactions YNAB imported from the linked accounts. |
| `transaction_ids` | array of string | Their ids, e.g. for find_transactions or approve_transactions. |
| `message` | string | What happened and what to do next, for the agent to relay. |

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget"
}
```

Antwort auf dem Demo-Budget:

```json
{
  "imported": 0,
  "transaction_ids": [],
  "message": "No new transaction to import."
}
```

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Ausstehende Transaktionen kategorisieren](/avenir-mcp/de/guides/classify/)
