---
title: "get_spending_trends"
description: "Spending per category, month by month, over the last N months."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Spending per category, month by month, over the last N months.

Use it for "is my grocery spending going up?" or to compare months. The result
maps each category name to its spending month by month, oldest first, as a
positive number in currency units. For a single month use get_category_balances
or get_budget_vs_actual; for the months ahead, forecast_balance. One YNAB
request for the list of months, then one per month; changes nothing.

## Comportamiento

| | |
|---|---|
| Tipo | solo lectura |
| Confirmación | no |
| Deshacer | no |
| Idempotente | sí |
| Peticiones a YNAB | 4 para el ejemplo de abajo, con la caché vacía |

## Parámetros

| Nombre | Tipo | Obligatorio | Por defecto | Descripción |
|---|---|---|---|---|
| `plan_id` | string | sí | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | no | `3` | Number of past months to include, 1 to 24 (default 3). |

## Devuelve

`object`


## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget",
  "months_count": 3
}
```

Respuesta sobre el presupuesto de demostración:

```json
{
  "Alquiler": [
    {
      "month": "2026-07-01",
      "amount": 950.0
    },
    {
      "month": "2026-08-01",
      "amount": 950.0
    },
    {
      "month": "2026-09-01",
      "amount": 950.0
    }
  ],
  "Luz": [
    {
      "month": "2026-07-01",
      "amount": 64.2
    },
    {
      "month": "2026-08-01",
      "amount": 64.2
    },
    {
      "month": "2026-09-01",
      "amount": 64.2
    }
  ],
  "Fibra": [
    {
      "month": "2026-07-01",
      "amount": 29.99
    },
    {
      "month": "2026-08-01",
      "amount": 29.99
    },
    {
      "month": "2026-09-01",
      "amount": 29.99
    }
  ],
  "Teléfono": [
    {
      "month": "2026-07-01",
      "amount": 19.99
    },
    {
      "month": "2026-08-01",
      "amount": 19.99
    },
    {
      "month": "2026-09-01",
      "amount": 19.99
    }
  ],
  "Supermercado": [
    {
      "month": "2026-07-01",
      "amount": 172.89
    },
    {
      "month": "2026-08-01",
      "amount": 192.51
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Restaurantes": [
    {
      "month": "2026-07-01",
      "amount": 61.5
    },
    {
      "month": "2026-08-01",
      "amount": 89.1
    },
    {
      "month": "2026-09-01",
      "amount": 142.5
    }
  ],
  "Transporte": [
    {
      "month": "2026-07-01",
      "amount": 45.0
    },
    {
      "month": "2026-08-01",
      "amount": 45.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Tenis": [
    {
      "month": "2026-07-01",
      "amount": 22.0
    },
    {
      "month": "2026-08-01",
      "amount": 22.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Suscripciones": [
    {
      "month": "2026-07-01",
      "amount": 13.49
    },
    {
      "month": "2026-08-01",
      "amount": 13.49
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ],
  "Vacaciones": [
    {
      "month": "2026-07-01",
      "amount": 0.0
    },
    {
      "month": "2026-08-01",
      "amount": 0.0
    },
    {
      "month": "2026-09-01",
      "amount": 0.0
    }
  ]
}
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Revisar un mes](/avenir-mcp/es/guides/monthly-review/)
