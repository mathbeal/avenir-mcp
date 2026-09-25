---
title: "Erreurs"
description: "Tous les messages d'erreur qu'Avenir peut renvoyer, outil par outil."
sidebar:
  order: 2
---

Une erreur revient comme un résultat d'outil marqué `isError`, avec un message qui dit quoi corriger, pour que l'agent puisse rectifier son appel. Les éléments entre accolades représentent la valeur transmise.

## Venant de YNAB

Tout outil qui appelle YNAB peut renvoyer l'erreur de YNAB : `Error calling tool '<tool>': YNAB <status>: <detail>` — par exemple `YNAB 401` pour un jeton faux ou révoqué, `YNAB 429` quand les 200 requêtes par heure sont épuisées. Sans `YNAB_API_KEY`, le serveur refuse d'appeler YNAB : `YNAB_API_KEY environment variable is not set`.

## [`forecast_balance`](/avenir-mcp/fr/reference/tools/forecast-balance/)

- `Unknown account(s) {unknown}: use ids from list_accounts.`
- `until must be the current month or later.`
- `until must be at most 24 months ahead.`
- `until must be a month as YYYY-MM, got '{until}'.`

## [`get_budget_vs_actual`](/avenir-mcp/fr/reference/tools/get-budget-vs-actual/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`get_category_balances`](/avenir-mcp/fr/reference/tools/get-category-balances/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`get_monthly_summary`](/avenir-mcp/fr/reference/tools/get-monthly-summary/)

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

## [`suggest_categories`](/avenir-mcp/fr/reference/tools/suggest-categories/)

- `Invalid cursor: pass the next_cursor value from the previous page unchanged, or omit it to start from the first page.`

## [`apply_categories`](/avenir-mcp/fr/reference/tools/apply-categories/)

- `Transaction {tx_id} is assigned twice: keep one assignment.`
- `Transaction {tx_id} is not in this budget: use the transaction_id values returned by suggest_categories.`
- `Category {category_id} is not in this budget: use a category_id from the categories returned by suggest_categories.`
- `Transaction {tx_id} is split across categories: change its lines in YNAB.`
- `Transaction {tx_id} is a transfer between accounts: YNAB gives it no category.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`create_category`](/avenir-mcp/fr/reference/tools/create-category/)

- `Group {category_group_id} is not in this budget: use an id from list_category_groups.`
- `The name is empty: give the new category a name.`
- `'{new_name}' already exists in {group}.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`create_transactions`](/avenir-mcp/fr/reference/tools/create-transactions/)

- `Account {account_id} is not in this budget: use an id from list_accounts.`
- `Give at least one transaction to create.`
- `{date} is in the future: YNAB only records transactions that happened.`
- `Category {category} is not in this budget: use a category_id from get_category_balances.`
- `date must be YYYY-MM-DD, got '{date}'.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`reconcile_account`](/avenir-mcp/fr/reference/tools/reconcile-account/)

- `Account {account_id} is not in this budget: use an id from list_accounts.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`set_category_budget`](/avenir-mcp/fr/reference/tools/set-category-budget/)

- `Category {category_id} is not in this budget: use a category_id from get_category_balances.`
- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`undo_operation`](/avenir-mcp/fr/reference/tools/undo-operation/)

- `Nothing to undo: no operation of this budget is still in effect with id {operation_id}.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

## [`update_category`](/avenir-mcp/fr/reference/tools/update-category/)

- `Category {category_id} is not in this budget: use a category_id from suggest_categories.`
- `Group {category_group_id} is not in this budget: use an id from list_category_groups.`
- `The new name is empty: give a name, or omit it to keep the current one.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`
