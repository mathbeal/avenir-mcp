---
title: "get_savings_rate"
description: "How much of the income was kept, month by month: income, spending, saved, rate."
---

:::note[Erzeugt]
Aus dem Code erzeugt mit `python -m docsgen`; ein Test schlägt fehl, sobald die Seite nicht mehr übereinstimmt. Die Beschreibungen stammen aus dem Code und bleiben auf Englisch: In dieser Sprache lesen Agenten sie.
:::

## Zweck

How much of the income was kept, month by month: income, spending, saved, rate.

Use it for "what's my savings rate?", "how much do I put aside each month?" or "am
I saving more than last spring?". Income is money in categorised to Ready to Assign
on the budget accounts; starting balances and transfers are not income. Spending is
money out of the budget accounts less refunds (money in categorised to a spending
category); transfers between budget accounts are left out, a transfer to a tracking
account holding an asset (savings, investments) is saved, a transfer to a tracking
loan is spending. Saved is income plus spending; rate is saved over income, in
percent, null for a month without income. Complete months only, from the budget's
first transaction. Relay the notes with the figures. Amounts in currency units,
spending negative. For spending per category use get_spending_trends. Three YNAB
requests: accounts, categories, transactions; changes nothing.

## Verhalten

| | |
|---|---|
| Art | nur lesend |
| Bestätigung | nein |
| Rückgängig | nein |
| Idempotent | ja |
| YNAB-Anfragen | 3 für das Beispiel unten, leerer Cache |

## Parameter

| Name | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plan_id` | string | ja | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | nein | `6` | Complete months to measure, before the current one, 1 to 24 (default 6). |

## Rückgabe

| Feld | Typ | Beschreibung |
|---|---|---|
| `message` | string | The conclusion in one sentence or two, for the agent to relay. |
| `months` | array of object | The complete months measured, oldest first. |
| `months[].month` | string | The month, YYYY-MM. |
| `months[].income` | number | Money in categorised to Ready to Assign. |
| `months[].spending` | number | Money out less refunds, negative; transfers to an asset tracking account excluded. |
| `months[].saved` | number | Income plus spending: what was kept; negative when more went out than came in. |
| `months[].rate` | number \| null | Saved over income, in percent to one decimal; null when nothing came in. |
| `income` | number | Income over the period. |
| `spending` | number | Spending over the period, negative. |
| `saved` | number | Saved over the period: income plus spending. |
| `rate` | number \| null | Saved over income for the whole period, in percent to one decimal; null when nothing came in. |
| `average_saved` | number | Saved per month, on average over the months measured. |
| `best_month` | string \| null | The month with the highest rate, YYYY-MM; null when no month had income. |
| `worst_month` | string \| null | The month with the lowest rate, YYYY-MM; null when no month had income. |
| `moved_to_tracking` | number | Money moved to tracking accounts that hold an asset over the period, part of saved. |
| `notes` | array of string | How the figures were counted, to tell the user. |

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
  "message": "Over the last 3 complete months, 9600.00 came in and 4188.09 went out: 5411.91 saved, 56.4 % of the income. Best month: 2026-07 (56.9 %), worst: 2026-08 (55.4 %).",
  "months": [
    {
      "month": "2026-06",
      "income": 3200.0,
      "spending": -1382.75,
      "saved": 1817.25,
      "rate": 56.8
    },
    {
      "month": "2026-07",
      "income": 3200.0,
      "spending": -1379.06,
      "saved": 1820.94,
      "rate": 56.9
    },
    {
      "month": "2026-08",
      "income": 3200.0,
      "spending": -1426.28,
      "saved": 1773.72,
      "rate": 55.4
    }
  ],
  "income": 9600.0,
  "spending": -4188.09,
  "saved": 5411.91,
  "rate": 56.4,
  "average_saved": 1803.97,
  "best_month": "2026-07",
  "worst_month": "2026-08",
  "moved_to_tracking": 0.0,
  "notes": [
    "Income is money in categorised to Ready to Assign on the budget accounts; starting balances and transfers, from a tracking account too, are not income.",
    "Spending is money out of the budget accounts less refunds (money in categorised to a spending category); transfers between budget accounts are left out.",
    "A transfer to a tracking account that holds an asset (savings, investments) is saved, not spent; a transfer to a tracking loan or debt is spending, as YNAB's budget counts it.",
    "Saved is income less spending: what stayed in the budget accounts or went to an asset outside them. The rate is saved over income.",
    "Only the last 3 of the 6 months hold budget transactions: the figures are over those."
  ]
}
```

## Fehler

Dieses Tool erzeugt keine eigenen Fehler; Fehler von YNAB kommen als `Error calling tool '<tool>': YNAB <status>: <detail>` zurück.

## Siehe auch

- [Einen Monat auswerten](/avenir-mcp/de/guides/monthly-review/)
