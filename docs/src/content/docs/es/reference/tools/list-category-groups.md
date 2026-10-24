---
title: "list_category_groups"
description: "List the category groups a category can be created in or moved to."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

List the category groups a category can be created in or moved to.

A group is a heading over categories: it holds no amount of its own, so nothing
here says what was budgeted or spent.
A group id goes to create_category, or to update_category as category_group_id.
For the money in each category use get_category_balances; to classify
transactions, suggest_categories. With several plans, pass the plan id from
list_plans: 'last-used' follows the plan last opened in YNAB. Hidden, deleted and
system groups are left out. One YNAB request; changes nothing.

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

## Devuelve

`array of object`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | YNAB id of the group, to pass as category_group_id. |
| `name` | string | Group name. |

## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget"
}
```

Respuesta sobre el presupuesto de demostración:

```json
[
  {
    "id": "grp-bills",
    "name": "Facturas"
  },
  {
    "id": "grp-everyday",
    "name": "Día a día"
  },
  {
    "id": "grp-fun",
    "name": "Ocio"
  },
  {
    "id": "grp-savings-goals",
    "name": "Metas de ahorro"
  }
]
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
