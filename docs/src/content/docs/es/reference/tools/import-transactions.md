---
title: "import_transactions"
description: "Import the latest transactions from the plan's linked bank accounts into YNAB."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Import the latest transactions from the plan's linked bank accounts into YNAB.

The same as pressing Import in YNAB: nothing is deleted or changed, and YNAB never
imports a transaction twice, so it is applied at once, without a preview. Use it
before classifying or reconciling, so that the list is complete. Accounts without
a bank connection are left as they are. Imported transactions stay unapproved for
the user to review; to take one back, delete it in YNAB.

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

## Devuelve

| Campo | Tipo | Descripción |
|---|---|---|
| `imported` | integer | Number of transactions YNAB imported from the linked accounts. |
| `transaction_ids` | array of string | Their ids, e.g. for find_transactions or approve_transactions. |
| `message` | string | What happened and what to do next, for the agent to relay. |

## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget"
}
```

Respuesta sobre el presupuesto de demostración:

```json
{
  "imported": 0,
  "transaction_ids": [],
  "message": "No new transaction to import."
}
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Clasificar transacciones pendientes](/avenir-mcp/es/guides/classify/)
