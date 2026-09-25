---
title: "update_category"
description: "Rename a category and/or move it to another group, after the user confirms."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Rename a category and/or move it to another group, after the user confirms.

Transactions and amounts stay attached to the category. Confirmation works as
for apply_categories. To revert, call again with the previous name and group,
which the result gives.

## Behaviour

| | |
|---|---|
| Kind | write — hidden unless `AVENIR_MCP_WRITE=1` |
| Confirmation | yes: previewed, then applied after the user agrees |
| Undo | no |
| Destructive | yes |
| Idempotent | yes |
| YNAB requests | 2 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `budget_id` | string | yes | — | YNAB budget UUID or 'last-used'. |
| `category_id` | string | yes | — | Category to change (from suggest_categories or list_category_groups). |
| `name` | string \| null | no | `null` | New name; omit to keep it. |
| `category_group_id` | string \| null | no | `null` | Group to move it to (from list_category_groups); omit to keep it. |
| `confirmation` | string \| null | no | `null` | Code from a previous "confirmation_required" result. |

## Returns

| Field | Type | Description |
|---|---|---|
| `status` | "applied" \| "confirmation_required" \| "declined" \| "nothing_to_do" | Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the user agrees), declined (the user said no), or nothing_to_do. |
| `message` | string | What happened and what to do next, for the agent to relay. |
| `category_id` | string | The category changed. |
| `from_name` | string | Name before. |
| `to_name` | string | Name after. |
| `from_group` | string | Group before. |
| `to_group` | string | Group after. |
| `confirmation` | string \| null | Single-use code confirming exactly this preview, valid 10 minutes; null unless status is confirmation_required. |

## Example

Arguments:

```json
{
  "budget_id": "demo-budget",
  "category_id": "cat-tennis",
  "name": "Sport"
}
```

Answer on the demo budget:

```json
{
  "status": "confirmation_required",
  "message": "Nothing changed yet. Change category 'Tennis' (Fun) to 'Sport' (Fun)? If the user agrees, call again with this code.",
  "category_id": "cat-tennis",
  "from_name": "Tennis",
  "to_name": "Sport",
  "from_group": "Fun",
  "to_group": "Fun",
  "confirmation": "<confirmation code>"
}
```

## Errors

- `Category {category_id} is not in this budget: use a category_id from suggest_categories.`
- `Group {category_group_id} is not in this budget: use an id from list_category_groups.`
- `The new name is empty: give a name, or omit it to keep the current one.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Organise categories](/avenir-mcp/guides/categories/)
