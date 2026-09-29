---
title: "Herramientas"
description: "Todas las herramientas que declara avenir-mcp: qué hacen, si leen o escriben, cuánto cuestan."
sidebar:
  order: 1
---

avenir-mcp declara estas herramientas. Las de lectura están siempre disponibles; las de escritura solo existen con `AVENIR_MCP_WRITE=1`, y todas salvo `approve_transactions` se previsualizan y se confirman.

## Lectura

| Herramienta | Resumen |
|---|---|
| [`find_transactions`](/avenir-mcp/es/reference/tools/find-transactions/) | Find transactions by date, amount, account, category or payee, categorised or not. |
| [`forecast_balance`](/avenir-mcp/es/reference/tools/forecast-balance/) | Project the balance month by month and say when money would run out. |
| [`get_budget_vs_actual`](/avenir-mcp/es/reference/tools/get-budget-vs-actual/) | Return a budget-vs-actual breakdown with utilisation percentage per category. |
| [`get_category_balances`](/avenir-mcp/es/reference/tools/get-category-balances/) | Budgeted, spent (activity) and available (balance) per category for a month. |
| [`get_monthly_summary`](/avenir-mcp/es/reference/tools/get-monthly-summary/) | A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories. |
| [`get_spending_trends`](/avenir-mcp/es/reference/tools/get-spending-trends/) | Return monthly spending trends per category over the last N months. |
| [`list_accounts`](/avenir-mcp/es/reference/tools/list-accounts/) | List the plan's accounts with their current balances (in currency units). |
| [`list_category_groups`](/avenir-mcp/es/reference/tools/list-category-groups/) | List the category groups a new category can be created in. |
| [`list_plans`](/avenir-mcp/es/reference/tools/list-plans/) | List all YNAB plans accessible with the current API key. |
| [`list_scheduled_transactions`](/avenir-mcp/es/reference/tools/list-scheduled-transactions/) | List the scheduled transactions due between two dates: bills, salary, transfers. |
| [`suggest_categories`](/avenir-mcp/es/reference/tools/suggest-categories/) | List the transactions waiting for a category, with a suggestion when history allows. |

## Escritura

| Herramienta | Resumen |
|---|---|
| [`apply_categories`](/avenir-mcp/es/reference/tools/apply-categories/) | Assign categories to transactions, after the user confirms, and journal it for undo. |
| [`approve_transactions`](/avenir-mcp/es/reference/tools/approve-transactions/) | Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge). |
| [`create_category`](/avenir-mcp/es/reference/tools/create-category/) | Create a category in a group, after the user confirms. |
| [`create_transactions`](/avenir-mcp/es/reference/tools/create-transactions/) | Create transactions on an account, e.g. ones the bank import missed, after the user confirms. |
| [`move_money`](/avenir-mcp/es/reference/tools/move-money/) | Move money budgeted in one category to another for a month, after the user confirms. |
| [`reconcile_account`](/avenir-mcp/es/reference/tools/reconcile-account/) | Compare an account with the balance your bank shows, then reconcile it. |
| [`set_category_budget`](/avenir-mcp/es/reference/tools/set-category-budget/) | Set the amount budgeted ("Assigned") in a category for a month, after the user confirms. |
| [`split_transaction`](/avenir-mcp/es/reference/tools/split-transaction/) | Split one transaction across categories, e.g. from a receipt, after the user confirms. |
| [`undo_operation`](/avenir-mcp/es/reference/tools/undo-operation/) | Undo an operation made through this server: the latest one, or the one named. |
| [`update_category`](/avenir-mcp/es/reference/tools/update-category/) | Rename a category and/or move it to another group, after the user confirms. |

## Recursos

| URI | Descripción |
|---|---|
| `avenir-mcp://guide` | How to use this server's tools, and the YNAB method in brief. |
| `ynab://plans` | The plans (budgets) the token can read, with the ids tools need. |
| `ynab://plans/{plan_id}/categories` | A plan's assignable categories by group, with their ids. |
| `ynab://plans/{plan_id}/accounts` | A plan's open accounts, balances in currency units. |

## Prompts

| Prompt | Argumentos | Descripción |
|---|---|---|
| `classify_pending` | `plan_id` | Classify the transactions waiting for a category. |
| `monthly_review` | `plan_id`, `month` (opcional) | Review a month of a plan: where the money went and what needs attention. |
| `reconcile` | `plan_id`, `account_id`, `bank_balance` | Reconcile an account with the balance the bank shows. |
| `plan_next_month` | `plan_id` | Prepare next month's category amounts from the forecast and this month's categories. |
