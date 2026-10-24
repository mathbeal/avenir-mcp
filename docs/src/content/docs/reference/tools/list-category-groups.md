---
title: "list_category_groups"
description: "List the category groups a category can be created in or moved to."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

List the category groups a category can be created in or moved to.

A group is a heading over categories: it holds no amount of its own, so nothing
here says what was budgeted or spent.
A group id goes to create_category, or to update_category as category_group_id.
For the money in each category use get_category_balances; to classify
transactions, suggest_categories. With several plans, pass the plan id from
list_plans: 'last-used' follows the plan last opened in YNAB. Hidden, deleted and
system groups are left out. One YNAB request; changes nothing.

## Behaviour

| | |
|---|---|
| Kind | read-only |
| Confirmation | no |
| Undo | no |
| Idempotent | yes |
| YNAB requests | 1 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `plan_id` | string | yes | — | YNAB plan id or 'last-used'. |

## Returns

`array of object`

| Field | Type | Description |
|---|---|---|
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

## Example

Arguments:

```json
{
  "plan_id": "demo-budget"
}
```

Answer on the demo budget:

```json
[
  {
    "id": "grp-bills",
    "name": "Bills"
  },
  {
    "id": "grp-everyday",
    "name": "Everyday"
  },
  {
    "id": "grp-fun",
    "name": "Fun"
  },
  {
    "id": "grp-savings-goals",
    "name": "Savings goals"
  }
]
```

## Errors

This tool raises no error of its own; YNAB's errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.
