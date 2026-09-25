---
title: "list_budgets"
description: "List all YNAB budgets accessible with the current API key."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

List all YNAB budgets accessible with the current API key.

Returns a list of budget dicts with id, name, first_month, last_month.
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
    "last_modified_on": "2026-09-20"
  }
]
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
