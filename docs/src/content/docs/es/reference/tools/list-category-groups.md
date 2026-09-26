---
title: "list_category_groups"
description: "List the category groups a new category can be created in."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

List the category groups a new category can be created in.

Hidden, deleted and system groups are left out. Pass a group id to
create_category.

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
    "name": "Bills"
  },
  {
    "id": "grp-everyday",
    "name": "Everyday"
  },
  {
    "id": "grp-fun",
    "name": "Fun"
  },
  {
    "id": "grp-savings-goals",
    "name": "Savings goals"
  }
]
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
