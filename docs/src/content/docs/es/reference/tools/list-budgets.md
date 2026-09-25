---
title: "list_budgets"
description: "List all YNAB budgets accessible with the current API key."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

List all YNAB budgets accessible with the current API key.

Returns a list of budget dicts with id, name, first_month, last_month.
Use the budget id (or 'last-used') in subsequent tool calls.

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
    "last_modified_on": "2026-09-20"
  }
]
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
