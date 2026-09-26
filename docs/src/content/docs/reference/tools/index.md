---
title: "Tools"
description: "Every tool avenir-mcp declares: what it does, whether it reads or writes, what it costs."
sidebar:
  order: 1
---

avenir-mcp declares these tools. Read-only tools are always available; write tools exist only with `AVENIR_MCP_WRITE=1`, and every one of them but `approve_transactions` is previewed and confirmed.

## Read

| Tool | Summary |
|---|---|
| [`find_transactions`](/avenir-mcp/reference/tools/find-transactions/) | Find transactions by date, exact amount and account, whether categorised or not. |
| [`forecast_balance`](/avenir-mcp/reference/tools/forecast-balance/) | Project the balance month by month and say when money would run out. |
| [`get_budget_vs_actual`](/avenir-mcp/reference/tools/get-budget-vs-actual/) | Return a budget-vs-actual breakdown with utilisation percentage per category. |
| [`get_category_balances`](/avenir-mcp/reference/tools/get-category-balances/) | Budgeted, spent (activity) and available (balance) per category for a month. |
| [`get_monthly_summary`](/avenir-mcp/reference/tools/get-monthly-summary/) | A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories. |
| [`get_spending_trends`](/avenir-mcp/reference/tools/get-spending-trends/) | Return monthly spending trends per category over the last N months. |
| [`list_accounts`](/avenir-mcp/reference/tools/list-accounts/) | List the budget's accounts with their current balances (in currency units). |
| [`list_budgets`](/avenir-mcp/reference/tools/list-budgets/) | List all YNAB budgets accessible with the current API key. |
| [`list_category_groups`](/avenir-mcp/reference/tools/list-category-groups/) | List the category groups a new category can be created in. |
| [`suggest_categories`](/avenir-mcp/reference/tools/suggest-categories/) | List the transactions waiting for a category, with a suggestion when history allows. |

## Write

| Tool | Summary |
|---|---|
| [`apply_categories`](/avenir-mcp/reference/tools/apply-categories/) | Assign categories to transactions, after the user confirms, and journal it for undo. |
| [`approve_transactions`](/avenir-mcp/reference/tools/approve-transactions/) | Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge). |
| [`create_category`](/avenir-mcp/reference/tools/create-category/) | Create a category in a group, after the user confirms. |
| [`create_transactions`](/avenir-mcp/reference/tools/create-transactions/) | Create transactions on an account, e.g. ones the bank import missed, after the user confirms. |
| [`reconcile_account`](/avenir-mcp/reference/tools/reconcile-account/) | Compare an account with the balance your bank shows, then reconcile it. |
| [`set_category_budget`](/avenir-mcp/reference/tools/set-category-budget/) | Set the amount budgeted ("Assigned") in a category for a month, after the user confirms. |
| [`split_transaction`](/avenir-mcp/reference/tools/split-transaction/) | Split one transaction across categories, e.g. from a receipt, after the user confirms. |
| [`undo_operation`](/avenir-mcp/reference/tools/undo-operation/) | Undo an operation made through this server: the latest one, or the one named. |
| [`update_category`](/avenir-mcp/reference/tools/update-category/) | Rename a category and/or move it to another group, after the user confirms. |

## Resources

| URI | Description |
|---|---|
| `avenir-mcp://guide` | How to use this server's tools, and the YNAB method in brief. |
| `ynab://budgets` | The budgets the token can read, with the ids tools need. |
| `ynab://budgets/{budget_id}/categories` | A budget's assignable categories by group, with their ids. |
| `ynab://budgets/{budget_id}/accounts` | A budget's open accounts, balances in currency units. |

## Prompts

| Prompt | Arguments | Description |
|---|---|---|
| `classify_pending` | `budget_id` | Classify the transactions waiting for a category. |
| `monthly_review` | `budget_id`, `month` (optional) | Review a budget month: where the money went and what needs attention. |
| `reconcile` | `budget_id`, `account_id`, `bank_balance` | Reconcile an account with the balance the bank shows. |
| `plan_next_month` | `budget_id` | Prepare next month's budget from the forecast and this month's categories. |
