---
title: "Tools"
description: "Alle Tools, die avenir-mcp bereitstellt: Zweck, lesend oder schreibend, Kosten."
sidebar:
  order: 1
---

avenir-mcp stellt diese Tools bereit. Lesende Tools sind immer verfügbar; schreibende existieren nur mit `AVENIR_MCP_WRITE=1`, und alle außer `approve_transactions` und `import_transactions` werden als Vorschau gezeigt und bestätigt.

## Lesen

| Tool | Kurzbeschreibung |
|---|---|
| [`find_transactions`](/avenir-mcp/de/reference/tools/find-transactions/) | Find transactions by date, amount, account, category or payee, categorised or not. |
| [`forecast_balance`](/avenir-mcp/de/reference/tools/forecast-balance/) | Project the balance month by month and say when money would run out. |
| [`get_budget_vs_actual`](/avenir-mcp/de/reference/tools/get-budget-vs-actual/) | Return a budget-vs-actual breakdown with utilisation percentage per category. |
| [`get_category_balances`](/avenir-mcp/de/reference/tools/get-category-balances/) | Budgeted, spent (activity) and available (balance) per category for a month. |
| [`get_monthly_summary`](/avenir-mcp/de/reference/tools/get-monthly-summary/) | A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories. |
| [`get_spending_trends`](/avenir-mcp/de/reference/tools/get-spending-trends/) | Return monthly spending trends per category over the last N months. |
| [`list_accounts`](/avenir-mcp/de/reference/tools/list-accounts/) | List the plan's accounts with their current balances (in currency units). |
| [`list_category_groups`](/avenir-mcp/de/reference/tools/list-category-groups/) | List the category groups a new category can be created in. |
| [`list_plans`](/avenir-mcp/de/reference/tools/list-plans/) | List all YNAB plans accessible with the current API key. |
| [`list_scheduled_transactions`](/avenir-mcp/de/reference/tools/list-scheduled-transactions/) | List the scheduled transactions due between two dates: bills, salary, transfers. |
| [`suggest_categories`](/avenir-mcp/de/reference/tools/suggest-categories/) | List the transactions waiting for a category, with a suggestion when history allows. |

## Schreiben

| Tool | Kurzbeschreibung |
|---|---|
| [`apply_categories`](/avenir-mcp/de/reference/tools/apply-categories/) | Assign categories to transactions, after the user confirms, and journal it for undo. |
| [`approve_transactions`](/avenir-mcp/de/reference/tools/approve-transactions/) | Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge). |
| [`create_category`](/avenir-mcp/de/reference/tools/create-category/) | Create a category in a group, after the user confirms. |
| [`create_transactions`](/avenir-mcp/de/reference/tools/create-transactions/) | Create transactions on an account, e.g. ones the bank import missed, after the user confirms. |
| [`import_transactions`](/avenir-mcp/de/reference/tools/import-transactions/) | Import the latest transactions from the plan's linked bank accounts into YNAB. |
| [`move_money`](/avenir-mcp/de/reference/tools/move-money/) | Move money budgeted in one category to another for a month, after the user confirms. |
| [`reconcile_account`](/avenir-mcp/de/reference/tools/reconcile-account/) | Compare an account with the balance your bank shows, then reconcile it. |
| [`set_category_budget`](/avenir-mcp/de/reference/tools/set-category-budget/) | Set the amount budgeted ("Assigned") in a category for a month, after the user confirms. |
| [`split_transaction`](/avenir-mcp/de/reference/tools/split-transaction/) | Split one transaction across categories, e.g. from a receipt, after the user confirms. |
| [`undo_operation`](/avenir-mcp/de/reference/tools/undo-operation/) | Undo an operation made through this server: the latest one, or the one named. |
| [`update_category`](/avenir-mcp/de/reference/tools/update-category/) | Rename a category and/or move it to another group, after the user confirms. |

## Ressourcen

| URI | Beschreibung |
|---|---|
| `avenir-mcp://guide` | How to use this server's tools, and the YNAB method in brief. |
| `ynab://plans` | The plans (budgets) the token can read, with the ids tools need. |
| `ynab://plans/{plan_id}/categories` | A plan's assignable categories by group, with their ids. |
| `ynab://plans/{plan_id}/accounts` | A plan's open accounts, balances in currency units. |

## Prompts

| Prompt | Argumente | Beschreibung |
|---|---|---|
| `classify_pending` | `plan_id` | Classify the transactions waiting for a category. |
| `monthly_review` | `plan_id`, `month` (optional) | Review a month of a plan: where the money went and what needs attention. |
| `reconcile` | `plan_id`, `account_id`, `bank_balance` | Reconcile an account with the balance the bank shows. |
| `plan_next_month` | `plan_id` | Prepare next month's category amounts from the forecast and this month's categories. |
