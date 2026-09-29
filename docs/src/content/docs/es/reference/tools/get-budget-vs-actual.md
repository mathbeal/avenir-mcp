---
title: "get_budget_vs_actual"
description: "Return a budget-vs-actual breakdown with utilisation percentage per category."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Return a budget-vs-actual breakdown with utilisation percentage per category.

Amounts in currency units; utilization_pct above 100 means over budget.

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
| `month` | string | no | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Devuelve

`array of object`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | YNAB id of the category. |
| `name` | string | Category name. |
| `group` | string | Name of the category's group, e.g. Fun for Tennis. |
| `budgeted` | number | Amount assigned to the category this month. |
| `actual` | number | Amount spent this month, as a positive number. |
| `balance` | number | What is left: budgeted minus spent, plus what was carried over; negative when overspent. |
| `utilization_pct` | number | Spent as a share of budgeted, in percent; above 100 means overspent, 0 when nothing is budgeted. |

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
    "id": "cat-rent",
    "name": "Alquiler",
    "group": "Facturas",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Luz",
    "group": "Facturas",
    "budgeted": 70.0,
    "actual": 0.0,
    "balance": 70.0,
    "utilization_pct": 0.0
  },
  {
    "id": "cat-phone",
    "name": "Teléfono",
    "group": "Facturas",
    "budgeted": 20.0,
    "actual": 19.99,
    "balance": 0.01,
    "utilization_pct": 99.9
  },
  {
    "id": "cat-groceries",
    "name": "Supermercado",
    "group": "Día a día",
    "budgeted": 400.0,
    "actual": 0.0,
    "balance": 400.0,
    "utilization_pct": 0.0
  },
  "… 5 more"
]
```

## Errores

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Los errores propios de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Revisar un mes](/avenir-mcp/es/guides/monthly-review/)
