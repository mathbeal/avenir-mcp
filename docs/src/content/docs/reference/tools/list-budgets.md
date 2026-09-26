---
title: "list_budgets"
description: "List all YNAB budgets accessible with the current API key."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

List all YNAB budgets accessible with the current API key.

Use the budget id in subsequent tool calls. 'last-used' also works, but names
whichever budget was last opened in YNAB: with several budgets, pass the id.

## Behaviour

| | |
|---|---|
| Kind | read-only |
| Confirmation | no |
| Undo | no |
| Idempotent | yes |
| YNAB requests | 1 for the example below, on a cold cache |

## Parameters

none.

## Returns

`array of object`

| Field | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the budget, to pass as budget_id. |
| `name` | string | Budget name. |
| `first_month` | string \| null | First month with data, YYYY-MM-01; null for an empty budget. |
| `last_month` | string \| null | Last month with data, YYYY-MM-01; null for an empty budget. |

## Example

Arguments:

```json
{}
```

Answer on the demo budget:

```json
[
  {
    "id": "demo-budget",
    "name": "Demo household",
    "first_month": "2026-06-01",
    "last_month": "2026-09-01"
  }
]
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
