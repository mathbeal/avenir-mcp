---
title: "get_spending_trends"
description: "Return monthly spending trends per category over the last N months."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

Return monthly spending trends per category over the last N months.

The result maps each category name to its spending month by month, oldest
first, in currency units.

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
| `months_count` | integer | nein | `3` | Number of past months to include (default 3). |

## Rückgabe

`object`


## Beispiel

Argumente:

```json
{
  "plan_id": "demo-budget",
  "months_count": 3
}
```

Antwort auf dem Demo-Budget:

```json
{
  "Rent": [
    {
      "month": "2026-07-01",
      "amount": 950.0
    },
    {
      "month": "2026-08-01",
      "amount": 950.0
    },
    {
      "month": "2026-09-01",
      "amount": 950.0
    }
  ],
  "Electricity": [
    {
      "month": "2026-07-01",
      "amount": 64.2
    },
    {
      "month": "2026-08-01",
      "amount": 64.2
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Phone": [
    {
      "month": "2026-07-01",
      "amount": 19.99
    },
    {
      "month": "2026-08-01",
      "amount": 19.99
    },
    {
      "month": "2026-09-01",
      "amount": 19.99
    }
  ],
  "Groceries": [
    {
      "month": "2026-07-01",
      "amount": 172.89
    },
    {
      "month": "2026-08-01",
      "amount": 192.51
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Restaurants": [
    {
      "month": "2026-07-01",
      "amount": 61.5
    },
    {
      "month": "2026-08-01",
      "amount": 89.1
    },
    {
      "month": "2026-09-01",
      "amount": 142.5
    }
  ],
  "Transport": [
    {
      "month": "2026-07-01",
      "amount": 45.0
    },
    {
      "month": "2026-08-01",
      "amount": 45.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Tennis": [
    {
      "month": "2026-07-01",
      "amount": 22.0
    },
    {
      "month": "2026-08-01",
      "amount": 22.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Subscriptions": [
    {
      "month": "2026-07-01",
      "amount": 13.49
    },
    {
      "month": "2026-08-01",
      "amount": 13.49
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Holidays": [
    {
      "month": "2026-07-01",
      "amount": 0.0
    },
    {
      "month": "2026-08-01",
      "amount": 0.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ]
}
```

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Einen Monat auswerten](/avenir-mcp/de/guides/monthly-review/)
