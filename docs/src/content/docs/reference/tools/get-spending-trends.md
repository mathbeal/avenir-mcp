---
title: "get_spending_trends"
description: "Return monthly spending trends per category over the last N months."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Return monthly spending trends per category over the last N months.

## Behaviour

| | |
|---|---|
| Kind | read-only |
| Confirmation | no |
| Undo | no |
| Idempotent | yes |
| YNAB requests | 4 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `budget_id` | string | yes | — | YNAB budget UUID or 'last-used'. |
| `months_count` | integer | no | `3` | Number of past months to include (default 3). |

## Returns

`object`


## Example

Arguments:

```json
{
  "budget_id": "demo-budget",
  "months_count": 3
}
```

Answer on the demo budget:

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

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Review a month](/avenir-mcp/guides/monthly-review/)
