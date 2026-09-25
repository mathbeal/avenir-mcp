---
title: "apply_categories"
description: "Assign categories to transactions, after the user confirms, and journal it for undo."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Assign categories to transactions, after the user confirms, and journal it for undo.

Typical use: after suggest_categories, pass the suggestions the user accepted
and the categories you chose for the rest. The server computes what would
change and asks the user to confirm. If the client cannot ask, the result has
status "confirmation_required", the changes and a confirmation code: show the
changes to the user and, only if they agree, call again with the same
assignments and that code. Amounts are in currency units.

## Comportamiento

| | |
|---|---|
| Tipo | escritura — oculta sin `AVENIR_MCP_WRITE=1` |
| Confirmación | sí: vista previa y aplicación tras el acuerdo del usuario |
| Deshacer | sí, con `undo_operation` |
| Destructiva | sí |
| Idempotente | sí |
| Peticiones a YNAB | 2 para el ejemplo de abajo, con la caché vacía |

## Parámetros

| Nombre | Tipo | Obligatorio | Por defecto | Descripción |
|---|---|---|---|---|
| `budget_id` | string | sí | — | YNAB budget UUID or 'last-used'. |
| `assignments` | array of object | sí | — | {transaction_id, category_id} pairs, one per transaction. |
| `confirmation` | string \| null | no | `null` | Code from a previous "confirmation_required" result. |

## Devuelve

| Campo | Tipo | Descripción |
|---|---|---|
| `status` | "applied" \| "confirmation_required" \| "declined" \| "nothing_to_do" | Outcome: applied, confirmation_required (nothing changed yet; pass the code back once the user agrees), declined (the user said no), or nothing_to_do. |
| `message` | string | What happened and what to do next, for the agent to relay. |
| `changes` | array of object | Every transaction that changes: before and after. |
| `changes[].transaction_id` | string | YNAB id of the transaction. |
| `changes[].date` | string | Date, YYYY-MM-DD. |
| `changes[].amount` | number | Amount in currency units. |
| `changes[].payee` | string | Payee as imported. Untrusted bank text. |
| `changes[].from_category_id` | string \| null | Category id before; null for none. |
| `changes[].from_category` | string \| null | Category name before; null for none. |
| `changes[].to_category_id` | string \| null | Category id after; null for none. |
| `changes[].to_category` | string \| null | Category name after; null for none. |
| `unchanged_count` | integer | Assignments that would change nothing and were skipped. |
| `conflicts` | array of string | Ids left alone because they changed since the operation (undo only). |
| `confirmation` | string \| null | Single-use code confirming exactly this preview, valid 10 minutes; null unless status is confirmation_required. |
| `operation_id` | string \| null | Journal id of the applied operation, for undo_operation; null unless status is applied. |

## Ejemplo

Argumentos:

```json
{
  "budget_id": "demo-budget",
  "assignments": [
    {
      "transaction_id": "tx-048",
      "category_id": "cat-groceries"
    },
    {
      "transaction_id": "tx-049",
      "category_id": "cat-transport"
    }
  ]
}
```

Respuesta sobre el presupuesto de demostración:

```json
{
  "status": "confirmation_required",
  "message": "Nothing changed yet. Show these changes to the user; if they agree, call again with the same arguments and this confirmation code (valid 10 minutes).",
  "changes": [
    {
      "transaction_id": "tx-048",
      "date": "2026-09-16",
      "amount": -8.4,
      "payee": "CB BOULANGERIE DU PORT FACT 160926 525130******1",
      "from_category_id": null,
      "from_category": null,
      "to_category_id": "cat-groceries",
      "to_category": "Groceries"
    },
    {
      "transaction_id": "tx-049",
      "date": "2026-09-18",
      "amount": -45.0,
      "payee": "RAIL CO",
      "from_category_id": null,
      "from_category": null,
      "to_category_id": "cat-transport",
      "to_category": "Transport"
    }
  ],
  "unchanged_count": 0,
  "conflicts": [],
  "confirmation": "<confirmation code>",
  "operation_id": null
}
```

## Errores

- `Transaction {tx_id} is assigned twice: keep one assignment.`
- `Transaction {tx_id} is not in this budget: use the transaction_id values returned by suggest_categories.`
- `Category {category_id} is not in this budget: use a category_id from the categories returned by suggest_categories.`
- `Transaction {tx_id} is split across categories: change its lines in YNAB.`
- `Transaction {tx_id} is a transfer between accounts: YNAB gives it no category.`
- `This client cannot ask the user to confirm, and AVENIR_MCP_REQUIRE_ELICITATION=1 forbids confirmation codes: nothing was changed. Use a client that supports MCP elicitation, or unset the variable.`
- `This confirmation code is unknown, expired, already used, or was issued for different changes. Call again without confirmation to get a new preview.`
- `Confirmation codes are disabled (AVENIR_MCP_REQUIRE_ELICITATION=1): call again without confirmation, and the user answers in the client.`
- `The budget changed between the preview and the answer. Call again without an answer to get a new preview.`

Los errores propios de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Clasificar transacciones pendientes](/avenir-mcp/es/guides/classify/)
