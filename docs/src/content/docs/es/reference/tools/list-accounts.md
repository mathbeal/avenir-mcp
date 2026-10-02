---
title: "list_accounts"
description: "List the plan's accounts with their balances, bank link and last reconciliation."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

List the plan's accounts with their balances, bank link and last reconciliation.

Use it to reconcile YNAB with the bank, and to tell the user when a bank link is
broken (no transaction comes in until they fix it in YNAB) or when an account has
not been reconciled for months. Its ids are the account_ids other tools take.
Balances are in currency units. Every account comes in one response, closed
ones included, in one YNAB request; changes nothing.

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
| `id` | string | YNAB id of the account. |
| `name` | string | Account name. |
| `type` | string | YNAB account type, e.g. checking, savings, creditCard, otherAsset. |
| `on_budget` | boolean | False for a tracking account, whose transactions take no category. |
| `closed` | boolean | True when the account is closed in YNAB. |
| `balance` | number | Balance of all transactions. |
| `cleared_balance` | number | Balance of the transactions the bank has shown. |
| `uncleared_balance` | number | Balance of the transactions the bank has not shown yet. |
| `bank_link` | "healthy" \| "broken" \| "none" | Whether YNAB imports this account from the bank: broken means the connection needs the user's attention in YNAB, and no new transaction will come in until then. |
| `last_reconciled` | string \| null | Date (YYYY-MM-DD) of the last reconciliation, or None if never reconciled. |

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
    "id": "acc-checking",
    "name": "Cuenta corriente",
    "type": "checking",
    "on_budget": true,
    "closed": false,
    "balance": 3328.5,
    "cleared_balance": 3328.5,
    "uncleared_balance": 0.0,
    "bank_link": "healthy",
    "last_reconciled": "2026-08-31"
  },
  {
    "id": "acc-savings",
    "name": "Ahorro",
    "type": "savings",
    "on_budget": true,
    "closed": false,
    "balance": 600.0,
    "cleared_balance": 600.0,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  {
    "id": "acc-joint-savings",
    "name": "Ahorro común",
    "type": "savings",
    "on_budget": false,
    "closed": false,
    "balance": 16342.36,
    "cleared_balance": 16342.36,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  {
    "id": "acc-car-loan",
    "name": "Préstamo del coche",
    "type": "autoLoan",
    "on_budget": false,
    "closed": false,
    "balance": -19040.81,
    "cleared_balance": -19040.81,
    "uncleared_balance": 0.0,
    "bank_link": "none",
    "last_reconciled": null
  },
  "… 2 more"
]
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.
