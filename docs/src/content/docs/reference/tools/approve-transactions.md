---
title: "approve_transactions"
description: "Mark transactions as approved, i.e. reviewed (clears YNAB's \"unapproved\" badge)."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

Only approve transactions whose category has been checked.

## Behaviour

| | |
|---|---|
| Kind | write — hidden unless `AVENIR_MCP_WRITE=1` |
| Confirmation | no |
| Undo | no |
| Destructive | no |
| Idempotent | yes |
| YNAB requests | 1 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `plan_id` | string | yes | — | YNAB plan id or 'last-used'. |
| `tx_ids` | array of string | yes | — | Transaction UUIDs to approve. |

## Returns

| Field | Type | Description |
|---|---|---|
| `approved` | integer | Number of transactions YNAB updated. |

## Example

Arguments:

```json
{
  "plan_id": "demo-budget",
  "tx_ids": [
    "tx-048",
    "tx-049"
  ]
}
```

Answer on the demo budget:

```json
{
  "approved": 2
}
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
