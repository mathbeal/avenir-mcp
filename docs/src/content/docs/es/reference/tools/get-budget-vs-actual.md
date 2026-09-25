---
title: "get_budget_vs_actual"
description: "Return a budget-vs-actual breakdown with utilisation percentage per category."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Return a budget-vs-actual breakdown with utilisation percentage per category.

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
| `budget_id` | string | sí | — | YNAB budget UUID or 'last-used'. |
| `month` | string | no | `"current"` | ISO month 'YYYY-MM-01' or 'current'. |

## Devuelve

`array of object`


## Ejemplo

Argumentos:

```json
{
  "budget_id": "demo-budget",
  "month": "2026-09-01"
}
```

Respuesta sobre el presupuesto de demostración:

```json
[
  {
    "id": "cat-rent",
    "name": "Rent",
    "budgeted": 950.0,
    "actual": 950.0,
    "balance": 0.0,
    "utilization_pct": 100.0
  },
  {
    "id": "cat-power",
    "name": "Electricity",
    "budgeted": 70.0,
    "actual": 0.0,
    "balance": 70.0,
    "utilization_pct": 0.0
  },
  {
    "id": "cat-phone",
    "name": "Phone",
    "budgeted": 20.0,
    "actual": 19.99,
    "balance": 0.01,
    "utilization_pct": 99.9
  },
  {
    "id": "cat-groceries",
    "name": "Groceries",
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
