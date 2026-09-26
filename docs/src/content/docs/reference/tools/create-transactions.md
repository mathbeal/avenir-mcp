---
title: "create_transactions"
description: "Create transactions on an account, e.g. ones the bank import missed, after the user confirms."
---

:::note[Generated]
Generated from the code by `python -m docsgen`; a test fails when it no longer matches.
:::

## What it does

Create transactions on an account, e.g. ones the bank import missed, after the user confirms.

Each transaction: date (YYYY-MM-DD, not in the future), amount in currency
units (negative for spending), payee_name, and optionally memo and
category_id. They are created cleared and, unless approved is true, left for
the user to approve in YNAB. undo_operation deletes them. Confirmation works
as for apply_categories.

## Behaviour

| | |
|---|---|
| Kind | write — hidden unless `AVENIR_MCP_WRITE=1` |
| Confirmation | yes: previewed, then applied after the user agrees |
| Undo | yes, with `undo_operation` |
| Destructive | no |
| Idempotent | no |
| YNAB requests | 2 for the example below, on a cold cache |

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `budget_id` | string | yes | — | YNAB budget UUID or 'last-used'. |
| `account_id` | string | yes | — | Account to add them to (from list_accounts). |
| `transactions` | array of object | yes | — | The transactions to create. |
| `approved` | boolean | no | `false` | Skip YNAB's review step. |
| `confirmation` | string \| null | no | `null` | Code from a previous "confirmation_required" result. |

## Returns

| Field | Type | Description |
|---|---|---|
| `status` | "applied" \| "confirmation_required" \| "declined" \| "nothing_to_do" | Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the user agrees), declined (the user said no), or nothing_to_do. |
| `message` | string | What happened and what to do next, for the agent to relay. |
| `account` | string | Account name. |
| `transactions` | array of object | The transactions, as they will be (or were) created. |
| `transactions[].date` | string | Date, YYYY-MM-DD. |
| `transactions[].amount` | number | Amount in currency units. |
| `transactions[].payee` | string | Payee name. |
| `transactions[].category` | string \| null | Category name; null if none was given. |
| `transactions[].memo` | string \| null | Note; null if none. |
| `created_ids` | array of string | YNAB ids of the created transactions; empty until applied. |
| `duplicate_import_ids` | array of string | Import ids YNAB refused as duplicates. |
| `confirmation` | string \| null | Single-use code confirming exactly this preview, valid 10 minutes; null unless status is confirmation_required. |
| `operation_id` | string \| null | Journal id of the applied operation, for undo_operation; null unless status is applied. |

## Example

Arguments:

```json
{
  "budget_id": "demo-budget",
  "account_id": "acc-checking",
  "transactions": [
    {
      "date": "2026-09-21",
      "amount": -32.4,
      "payee_name": "Pharmacie Centrale",
      "memo": "not imported by the bank"
    }
  ]
}
```

Answer on the demo budget:

```json
{
  "status": "confirmation_required",
  "message": "Nothing changed yet. Create 1 transaction(s) on Checking?\n- 2026-09-21 Pharmacie Centrale -32.40 (no category) If the user agrees, call again with this code.",
  "account": "Checking",
  "transactions": [
    {
      "date": "2026-09-21",
      "amount": -32.4,
      "payee": "Pharmacie Centrale",
      "category": null,
      "memo": "not imported by the bank"
    }
  ],
  "created_ids": [],
  "duplicate_import_ids": [],
  "confirmation": "<confirmation code>",
  "operation_id": null
}
```

## Errors

- `Account {account_id} is not in this budget: use an id from list_accounts.`
- `Give at least one transaction to create.`
- `{date} is in the future: YNAB only records transactions that happened.`
- `Category {category} is not in this budget: use a category_id from get_category_balances.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

YNAB's own errors come back as `Error calling tool '<tool>': YNAB <status>: <detail>`.

## See also

- [Add missing transactions](/avenir-mcp/guides/missing-transactions/)
