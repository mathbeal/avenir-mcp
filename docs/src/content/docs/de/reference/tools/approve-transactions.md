---
title: "approve_transactions"
description: "Mark transactions as approved, i.e. reviewed (clears YNAB's \"unapproved\" badge)."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

Only approve transactions whose category has been checked.

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
| `tx_ids` | array of string | ja | — | Transaction UUIDs to approve. |

## Rückgabe

| Feld | Typ | Beschreibung |
|---|---|---|
| `approved` | integer | Number of transactions YNAB updated. |

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget",
  "tx_ids": [
    "tx-048",
    "tx-049"
  ]
}
```

Antwort auf dem Demo-Budget:

```json
{
  "approved": 2
}
```

## Fehler

Dieses Werkzeug erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.
