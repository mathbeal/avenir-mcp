---
title: "get_net_worth_trend"
description: "Assets, debts and net worth at the end of each month, to see debts go down."
---

:::note[Generado]
Generado desde el código con `python -m docsgen`; una prueba falla si deja de coincidir. Las descripciones vienen del código y se mantienen en inglés: es el idioma en que las leen los agentes.
:::

## Qué hace

Assets, debts and net worth at the end of each month, to see debts go down.

Use it for "is my debt going down?", "am I paying off my loans?" or "how did my net
worth change over the year?". Every account counts, tracking ones included: credit
cards, lines of credit, loans, mortgages and other liabilities are debts; every other
account is an asset. A closed account counts for the months it still had a balance.
months_count counts back from the current month, included, so 1 gives this month
alone and the default 12 the year up to it, however long the plan has existed. Each
month is read on its last day, the current one included: today's balance less the
transactions dated after that day, so this month already counts what is entered
for the days left. Amounts in currency units; debts are
negative, as YNAB shows them, and net_worth is assets plus debts. For each account's
balance today use list_accounts; for the months ahead, forecast_balance. Two YNAB
requests: accounts, transactions; changes nothing.

## Comportamiento

| | |
|---|---|
| Tipo | solo lectura |
| Confirmación | no |
| Deshacer | no |
| Idempotente | sí |
| Peticiones a YNAB | 2 para el ejemplo de abajo, con la caché vacía |

## Parámetros

| Nombre | Tipo | Obligatorio | Por defecto | Descripción |
|---|---|---|---|---|
| `plan_id` | string | sí | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | no | `12` | Number of months to show, the current one included, 1 to 24 (default 12). |

## Devuelve

| Campo | Tipo | Descripción |
|---|---|---|
| `months` | array of object | One entry per month, oldest first. |
| `months[].month` | string | The month, YYYY-MM-01; its figures are those of its last day, today for this month. |
| `months[].assets` | number | Balance of the asset accounts: checking, savings, cash, other assets. |
| `months[].debts` | number | Balance of the debt accounts (cards, loans, mortgages), negative while money is owed. |
| `months[].net_worth` | number | Assets plus debts: what would be left if every debt were paid. |
| `first_net_worth` | number | Net worth at the end of the first month shown. |
| `last_net_worth` | number | Net worth at the end of the last month shown: today's. |
| `change` | number | Last minus first: positive when the net worth grew. |
| `accounts` | array of string | Names of the accounts counted: the open ones, and the closed ones that still had a balance at one of these month ends. |

## Ejemplo

Argumentos:

```json
{
  "plan_id": "demo-budget",
  "months_count": 18
}
```

Respuesta sobre el presupuesto de demostración:

```json
{
  "months": [
    {
      "month": "2025-04-01",
      "assets": 3159.6,
      "debts": -27197.81,
      "net_worth": -24038.21
    },
    {
      "month": "2025-05-01",
      "assets": 4234.45,
      "debts": -26644.06,
      "net_worth": -22409.61
    },
    {
      "month": "2025-06-01",
      "assets": 5254.15,
      "debts": -26088.74,
      "net_worth": -20834.59
    },
    {
      "month": "2025-07-01",
      "assets": 6129.4,
      "debts": -25531.85,
      "net_worth": -19402.45
    },
    {
      "month": "2025-08-01",
      "assets": 5570.8,
      "debts": -24973.39,
      "net_worth": -19402.59
    },
    {
      "month": "2025-09-01",
      "assets": 6680.6,
      "debts": -24413.35,
      "net_worth": -17732.75
    },
    {
      "month": "2025-10-01",
      "assets": 7814.7,
      "debts": -23851.73,
      "net_worth": -16037.03
    },
    {
      "month": "2025-11-01",
      "assets": 8882.35,
      "debts": -23288.52,
      "net_worth": -14406.17
    },
    {
      "month": "2025-12-01",
      "assets": 8382.35,
      "debts": -22723.71,
      "net_worth": -14341.36
    },
    {
      "month": "2026-01-01",
      "assets": 9601.9,
      "debts": -22157.3,
      "net_worth": -12555.4
    },
    {
      "month": "2026-02-01",
      "assets": 10783.8,
      "debts": -21589.29,
      "net_worth": -10805.49
    },
    {
      "month": "2026-03-01",
      "assets": 13674.21,
      "debts": -20986.77,
      "net_worth": -7312.56
    },
    {
      "month": "2026-04-01",
      "assets": 15014.96,
      "debts": -20665.47,
      "net_worth": -5650.51
    },
    {
      "month": "2026-05-01",
      "assets": 16342.36,
      "debts": -20342.97,
      "net_worth": -4000.61
    },
    {
      "month": "2026-06-01",
      "assets": 17500.69,
      "debts": -20019.26,
      "net_worth": -2518.57
    },
    {
      "month": "2026-07-01",
      "assets": 18646.42,
      "debts": -19694.33,
      "net_worth": -1047.91
    },
    {
      "month": "2026-08-01",
      "assets": 19784.25,
      "debts": -19368.18,
      "net_worth": 416.07
    },
    {
      "month": "2026-09-01",
      "assets": 19476.84,
      "debts": -19040.81,
      "net_worth": 436.03
    }
  ],
  "first_net_worth": -24038.21,
  "last_net_worth": 436.03,
  "change": 24474.24,
  "accounts": [
    "Cuenta corriente",
    "Ahorro",
    "Ahorro común",
    "Préstamo del coche",
    "Préstamo de estudios",
    "Banco anterior"
  ]
}
```

## Errores

Esta herramienta no lanza errores propios; los errores de YNAB llegan como `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Ver también

- [Planificar](/avenir-mcp/es/guides/plan-ahead/)
