---
title: "get_spending_trends"
description: "Return monthly spending trends per category over the last N months."
---

:::note[Généré]
Généré depuis le code par `python -m docsgen` ; un test échoue s'il ne correspond plus. Les descriptions viennent du code et restent en anglais : c'est la langue dans laquelle les agents les lisent.
:::

## Rôle

Return monthly spending trends per category over the last N months.

The result maps each category name to its spending month by month, oldest
first, in currency units.

## Comportement

| | |
|---|---|
| Nature | lecture seule |
| Confirmation | non |
| Annulation | non |
| Idempotent | oui |
| Requêtes YNAB | 4 pour l'exemple ci-dessous, cache vide |

## Paramètres

| Nom | Type | Obligatoire | Défaut | Description |
|---|---|---|---|---|
| `plan_id` | string | oui | — | YNAB plan id or 'last-used'. |
| `months_count` | integer | non | `3` | Number of past months to include, 1 to 24 (default 3). |

## Retour

`object`


## Exemple

Arguments :

```json
{
  "plan_id": "demo-budget",
  "months_count": 3
}
```

Réponse sur le budget de démonstration :

```json
{
  "Loyer": [
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
  "Électricité": [
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
  "Box internet": [
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
  "Téléphone": [
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
  "Courses": [
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
  "Restaurants": [
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
  "Transports": [
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
  "Tennis": [
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
  "Abonnements": [
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
  "Vacances": [
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

## Erreurs

Cet outil ne lève pas d'erreur propre ; les erreurs de YNAB reviennent sous la forme `Error calling tool '<tool>': YNAB <status>: <detail>`.

## Voir aussi

- [Faire le point sur un mois](/avenir-mcp/fr/guides/monthly-review/)
