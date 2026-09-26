---
title: "get_category_balances"
description: "Budgeted, spent (activity) and available (balance) per category for a month."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Budgeted, spent (activity) and available (balance) per category for a month.

Amounts in currency units; activity is negative for spending. Hidden and
internal categories are left out, and so are categories with nothing
budgeted, spent or available unless include_empty is true. Use
get_budget_vs_actual for the share of each budget consumed.

## Comportamiento

| | |
|---|---|
| Tipo | solo lectura |
| Confirmación | no |
| Deshacer | no |
| Idempotente | sí |
| Peticiones a YNAB | 1 para el ejemplo de abajo, con la caché vacía |

## Parámetros

| Nombre | Tipo | Obligatorio | Por defecto | Descripción |
|---|---|---|---|---|
| `plan_id` | string | sí | — | YNAB plan id or 'last-used'. |
| `month` | string | no | `"current"` | 'YYYY-MM-01' or 'current'. |
| `include_empty` | boolean | no | `false` | Also list categories with no amount at all. |

## Devuelve

`array of object`

| Campo | Tipo | Descripción |
|---|---|---|
| `category_id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group. |
| `budgeted` | number | Amount assigned to the category this month. |
| `activity` | number | Amount spent (negative) or received in the category this month. |
| `balance` | number | Available at the end of the month: carried over, plus budgeted, plus activity. |

## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget",
  "month": "2026-09-01"
}
```

Respuesta sobre el presupuesto de demostración:

```json
[
  {
    "category_id": "cat-rent",
    "name": "Rent",
    "group": "Bills",
    "budgeted": 950.0,
    "activity": -950.0,
    "balance": 0.0
  },
  {
    "category_id": "cat-power",
    "name": "Electricity",
    "group": "Bills",
    "budgeted": 70.0,
    "activity": 0.0,
    "balance": 70.0
  },
  {
    "category_id": "cat-phone",
    "name": "Phone",
    "group": "Bills",
    "budgeted": 20.0,
    "activity": -19.99,
    "balance": 0.01
  },
  {
    "category_id": "cat-groceries",
    "name": "Groceries",
    "group": "Everyday",
    "budgeted": 400.0,
    "activity": 0.0,
    "balance": 400.0
  },
  "… 5 more"
]
```

## Errores

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Los errores propios de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Revisar un mes](/avenir-mcp/es/guides/monthly-review/)
