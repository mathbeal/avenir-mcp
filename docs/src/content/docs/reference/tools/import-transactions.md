---
title: "import_transactions"
description: "Import the latest transactions from the plan's linked bank accounts into YNAB."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Import the latest transactions from the plan's linked bank accounts into YNAB.

The same as pressing Import in YNAB: nothing is deleted or changed, and YNAB never
imports a transaction twice, so it is applied at once, without a preview. Use it
before classifying or reconciling, so that the list is complete. Accounts without
a bank connection are left as they are. Imported transactions stay unapproved for
the user to review; to take one back, delete it in YNAB.

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

## Returns

| Field | Type | Description |
|---|---|---|
| `imported` | integer | Number of transactions YNAB imported from the linked accounts. |
| `transaction_ids` | array of string | Their ids, e.g. for find_transactions or approve_transactions. |
| `message` | string | What happened and what to do next, for the agent to relay. |

## Example

Arguments:

```json
{
  "plan_id": "demo-budget"
}
```

Answer on the demo budget:

```json
{
  "imported": 0,
  "transaction_ids": [],
  "message": "No new transaction to import."
}
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Classify pending transactions](/avenir-mcp/guides/classify/)
