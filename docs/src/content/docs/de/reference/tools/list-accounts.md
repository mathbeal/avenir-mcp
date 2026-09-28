---
title: "list_accounts"
description: "List the plan's accounts with their current balances (in currency units)."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

List the plan's accounts with their current balances (in currency units).

Use it to reconcile YNAB with the bank.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 1 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |

## Rückgabe

`array of object`

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | string | YNAB id of the account. |
| `name` | string | Account name. |
| `type` | string | YNAB account type, e.g. checking, savings, creditCard, otherAsset. |
| `on_budget` | boolean | False for a tracking account, whose transactions take no category. |
| `closed` | boolean | True when the account is closed in YNAB. |
| `balance` | number | Balance of all transactions. |
| `cleared_balance` | number | Balance of the transactions the bank has shown. |
| `uncleared_balance` | number | Balance of the transactions the bank has not shown yet. |

## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget"
}
```

Antwort auf dem Demo-Budget:

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

## Fehler

Dieses Werkzeug erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.
