---
title: "get_net_worth_trend"
description: "Assets, debts and net worth at the end of each month, to see debts go down."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Assets, debts and net worth at the end of each month, to see debts go down.

Use it for "is my debt going down?", "am I paying off my loans?" or "how did my net
worth change over the year?". Every account counts, tracking ones included: credit
cards, lines of credit, loans, mortgages and other liabilities are debts; every other
account is an asset. A closed account counts for the months it still had a balance.
Each month end is today's balance less the transactions dated after it; the current
month shows today's balances. Amounts in currency units; debts are negative, as YNAB
shows them, and net_worth is assets plus debts. For each account's balance today use
list_accounts; for the months ahead, forecast_balance. Two YNAB requests: accounts,
transactions; changes nothing.

## Comportement

| | |
|---|---|
| Nature | lecture seule |
| Confirmation | non |
| Annulation | non |
| Idempotent | oui |
| Requêtes YNAB | 2 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `plan_id` | string | oui | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | non | `12` | Number of months to show, the current one included, 1 to 24 (default 12). |

## Retour

| Champ | Type | Description |
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

## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget",
  "months_count": 18
}
```

Réponse sur le budget de démonstration :

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
      "assets": 17759.61,
      "debts": -20019.26,
      "net_worth": -2259.65
    },
    {
      "month": "2026-07-01",
      "assets": 19180.55,
      "debts": -19694.33,
      "net_worth": -513.78
    },
    {
      "month": "2026-08-01",
      "assets": 20554.27,
      "debts": -19368.18,
      "net_worth": 1186.09
    },
    {
      "month": "2026-09-01",
      "assets": 20270.86,
      "debts": -19040.81,
      "net_worth": 1230.05
    }
  ],
  "first_net_worth": -24038.21,
  "last_net_worth": 1230.05,
  "change": 25268.26,
  "accounts": [
    "Compte courant",
    "Épargne",
    "Livret du foyer",
    "Crédit auto",
    "Prêt étudiant",
    "Ancienne banque"
  ]
}
```

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Anticiper](/avenir-mcp/fr/guides/plan-ahead/)
