---
title: "list_plans"
description: "List all YNAB plans accessible with the current API key."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

List all YNAB plans accessible with the current API key.

A plan is what YNAB now calls a budget, and what users may still call their budget.
Use the plan id in subsequent tool calls. 'last-used' also works, but names
whichever plan was last opened in YNAB: with several plans, pass the id.

## Comportamiento

| | |
|---|---|
| Tipo | solo lectura |
| Confirmación | no |
| Deshacer | no |
| Idempotente | sí |
| Peticiones a YNAB | 1 para el ejemplo de abajo, con la caché vacía |

## Parámetros

ninguno.

## Devuelve

`array of object`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | YNAB id of the budget, to pass as plan_id. |
| `name` | string | Budget name. |
| `first_month` | string \| null | First month with data, YYYY-MM-01; null for an empty budget. |
| `last_month` | string \| null | Last month with data, YYYY-MM-01; null for an empty budget. |

## Ejemplo

Argumentos:

```json
{}
```

Respuesta sobre el presupuesto de demostración:

```json
[
  {
    "id": "demo-budget",
    "name": "Demo household",
    "first_month": "2026-06-01",
    "last_month": "2026-09-01"
  }
]
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
