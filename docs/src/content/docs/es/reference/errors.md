---
title: "Errores"
description: "Todos los mensajes de error que puede devolver avenir-mcp, herramienta por herramienta."
sidebar:
  order: 2
---

Un error llega como resultado de herramienta marcado con `isError`, con un mensaje que dice qué corregir, para que el agente pueda rectificar su llamada. Lo que va entre llaves representa el valor enviado.

## Procedentes de YNAB

Cualquier herramienta que llame a YNAB puede devolver el error de YNAB: `Error calling tool '<tool>': YNAB <status>: <detail>` — por ejemplo `YNAB 401` si el token es incorrecto o está revocado, `YNAB 429` cuando se agotan las 200 peticiones por hora. Sin `YNAB_API_KEY`, el servidor se niega a llamar a YNAB: `YNAB_API_KEY environment variable is not set`.

## [`find_transactions`](/avenir-mcp/es/reference/tools/find-transactions/)

- `Account {0} is not in this plan: use an id from list_accounts.`
- `Category {0} is not in this plan: use a category_id from get_category_balances.`
- `until_date {until} is before since_date {since}: swap them.`
- `The dates span more than 366 days: search a shorter period.`

## [`forecast_balance`](/avenir-mcp/es/reference/tools/forecast-balance/)

- `Unknown account(s) {unknown}: use ids from list_accounts.`
- `until must be the current month or later.`
- `until must be at most 24 months ahead.`
- `until must be a month as YYYY-MM, got '{until}'.`

## [`get_budget_vs_actual`](/avenir-mcp/es/reference/tools/get-budget-vs-actual/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`get_category_balances`](/avenir-mcp/es/reference/tools/get-category-balances/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`get_monthly_summary`](/avenir-mcp/es/reference/tools/get-monthly-summary/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`list_scheduled_transactions`](/avenir-mcp/es/reference/tools/list-scheduled-transactions/)

- `Account {0} is not in this plan: use an id from list_accounts.`
- `Category {0} is not in this plan: use a category_id from get_category_balances.`
- `until_date {until} is before since_date {since}: swap them.`
- `The dates span more than 366 days: search a shorter period.`

## [`suggest_categories`](/avenir-mcp/es/reference/tools/suggest-categories/)

- `Invalid cursor: pass the next_cursor value from the previous page unchanged, or omit it to start from the first page.`

## [`apply_categories`](/avenir-mcp/es/reference/tools/apply-categories/)

- `Transaction {tx_id} is assigned twice: keep one assignment.`
- `Transaction {tx_id} is not in this plan: use the transaction_id values returned by suggest_categories.`
- `Category {category_id} is YNAB's internal Uncategorized: choose a real category.`
- `Category {category_id} is not in this plan: use a category_id from the categories returned by suggest_categories.`
- `Transaction {tx_id} is split across categories: change its lines in YNAB.`
- `Transaction {tx_id} is on an off-budget account: YNAB gives it no category.`
- `Transaction {tx_id} is a transfer between accounts: YNAB gives it no category.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`create_category`](/avenir-mcp/es/reference/tools/create-category/)

- `Group {category_group_id} is not in this plan: use an id from list_category_groups.`
- `The name is empty: give the new category a name.`
- `'{new_name}' already exists in {group}.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`create_transactions`](/avenir-mcp/es/reference/tools/create-transactions/)

- `Account {account_id} is not in this plan: use an id from list_accounts.`
- `Give at least one transaction to create.`
- `{date} is in the future: YNAB only records transactions that happened.`
- `Category {category} is not in this plan: use a category_id from get_category_balances.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`move_money`](/avenir-mcp/es/reference/tools/move-money/)

- `Give two different categories: money moves from one to another.`
- `Category {category_id} is not in this plan: use a category_id from get_category_balances.`
- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`
- `{refused}; {name} is back to {from_amount}: nothing was moved.`
- `{refused}, then putting {name} back failed too ({again}): set {name} back to {from_amount} in YNAB.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`reconcile_account`](/avenir-mcp/es/reference/tools/reconcile-account/)

- `Account {account_id} is not in this plan: use an id from list_accounts.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`set_category_budget`](/avenir-mcp/es/reference/tools/set-category-budget/)

- `Category {category_id} is not in this plan: use a category_id from get_category_balances.`
- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`split_transaction`](/avenir-mcp/es/reference/tools/split-transaction/)

- `Transaction {transaction_id} is not in this plan: use a transaction_id returned by suggest_categories.`
- `Transaction {tx_id} was deleted in YNAB: there is nothing to split.`
- `Transaction {tx_id} is already split: YNAB's API cannot change its lines, change them in YNAB.`
- `Transaction {tx_id} is a transfer between accounts: it cannot be split.`
- `Transaction {tx_id} is on an off-budget account: YNAB does not split those.`
- `Give at least two lines: to give the whole transaction one category, use apply_categories.`
- `The lines add up to {total}, the transaction is {amount}: they must match to the cent.`
- `A line is zero: leave it out.`
- `Category {category_id} is YNAB's internal Uncategorized: choose a real category.`
- `Category {category_id} is not in this plan: use a category_id from suggest_categories or get_category_balances.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`undo_operation`](/avenir-mcp/es/reference/tools/undo-operation/)

- `Nothing to undo: no operation of this plan is still in effect with id {operation_id}.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`update_category`](/avenir-mcp/es/reference/tools/update-category/)

- `Category {category_id} is not in this plan: use a category_id from suggest_categories.`
- `Group {category_group_id} is not in this plan: use an id from list_category_groups.`
- `The new name is empty: give a name, or omit it to keep the current one.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The plan changed between the preview and the answer. Call again without an answer to get a new preview.`
