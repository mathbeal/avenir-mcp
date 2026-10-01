---
title: "list_accounts"
description: "List the plan's accounts with their balances, bank link and last reconciliation."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

List the plan's accounts with their balances, bank link and last reconciliation.

Use it to reconcile YNAB with the bank, and to tell the user when a bank link is
broken (no transaction comes in until they fix it in YNAB) or when an account has
not been reconciled for months. Balances are in currency units.

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
| `bank_link` | "healthy" \| "broken" \| "none" | Whether YNAB imports this account from the bank: broken means the connection needs the user's attention in YNAB, and no new transaction will come in until then. |
| `last_reconciled` | string \| null | Date (YYYY-MM-DD) of the last reconciliation, or None if never reconciled. |

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
    "name": "Girokonto",
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
    "name": "Sparkonto",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  }
]
```

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.
