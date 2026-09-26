---
title: "approve_transactions"
description: "Mark transactions as approved, i.e. reviewed (clears YNAB's \"unapproved\" badge)."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Mark transactions as approved, i.e. reviewed (clears YNAB's "unapproved" badge).

Only approve transactions whose category has been checked.

## Comportamiento

| | |
|---|---|
| Tipo | escritura — oculta sin `AVENIR_MCP_WRITE=1` |
| Confirmación | no |
| Deshacer | no |
| Destructiva | no |
| Idempotente | sí |
| Peticiones a YNAB | 1 para el ejemplo de abajo, con la caché vacía |

## Parámetros

| Nombre | Tipo | Obligatorio | Por defecto | Descripción |
|---|---|---|---|---|
| `plan_id` | string | sí | — | YNAB plan id or 'last-used'. |
| `tx_ids` | array of string | sí | — | Transaction UUIDs to approve. |

## Devuelve

| Campo | Tipo | Descripción |
|---|---|---|
| `approved` | integer | Number of transactions YNAB updated. |

## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget",
  "tx_ids": [
    "tx-048",
    "tx-049"
  ]
}
```

Respuesta sobre el presupuesto de demostración:

```json
{
  "approved": 2
}
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
