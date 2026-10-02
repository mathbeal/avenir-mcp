---
title: "get_monthly_summary"
description: "A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

A month at a glance: income, budgeted, spent, Ready to Assign, overspent categories.

Use it first to review a month. Amounts in currency units; activity is negative
for spending. Only overspent categories are listed: use get_category_balances
for all of them, get_spending_trends to compare with earlier months, and
forecast_balance for the months ahead. One YNAB request; changes nothing.

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

## Devuelve

| Campo | Tipo | Descripción |
|---|---|---|
| `month` | string | First day of the month, YYYY-MM-01. |
| `income` | number | Money received in the month and assigned to Ready to Assign. |
| `budgeted` | number | Total assigned to categories in the month. |
| `activity` | number | Total spent (negative) and received in categories during the month. |
| `ready_to_assign` | number | Money not yet given a job; negative when more was assigned than received. |
| `age_of_money` | integer \| null | Days between receiving money and spending it, as YNAB computes it; null when unknown. |
| `overspent` | array of object | Categories whose available balance is negative this month. |
| `overspent[].category_id` | string | YNAB id of the category. |
| `overspent[].name` | string | Category name. |
| `overspent[].group` | string | Name of the category's group. |
| `overspent[].balance` | number | Available balance, negative: the amount overspent, in currency units. |

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
{
  "month": "2026-09-01",
  "income": 0.0,
  "budgeted": 1967.67,
  "activity": -1206.68,
  "ready_to_assign": 1729.32,
  "age_of_money": 47,
  "overspent": [
    {
      "category_id": "cat-restaurants",
      "name": "Restaurantes",
      "group": "Día a día",
      "balance": -22.5
    }
  ]
}
```

## Errores

- `month must be 'current' or the first day of a month as YYYY-MM-01, got '{month}'.`

Los errores propios de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Revisar un mes](/avenir-mcp/es/guides/monthly-review/)
