# Your first conversation

A short tour of what Avenir can do, in the order most people discover it. Every
answer shown is what Avenir really returns on the invented demo budget.

## 1. Look around

> **You:** What accounts do I have, and how much is on them?

```json
--8<-- "snippets/list_accounts.json"
```

Amounts are in your budget's currency, never in YNAB's internal *milliunits*.

## 2. See how the month is going

> **You:** How is September going?

```json
--8<-- "snippets/monthly_summary.json"
```

Only overspent categories are listed. Ask for detail when you want it:

> **You:** Show me every category for September.

```json
--8<-- "snippets/category_balances.json"
```

## 3. Tidy up

> **You:** What still needs a category?

```json
--8<-- "snippets/suggest_categories.json"
```

Where your history is clear, a `suggestion` is ready; for the rest, Claude proposes a
category and asks you. Continue with [Classify pending transactions](../use-cases/classify.md).

## 4. Change something — safely

> **You:** Yes, put the bakery in Groceries and the train in Transport.

Nothing changes yet. You see exactly what will:

```json
--8<-- "snippets/apply_preview.json"
```

Depending on your client, it asks you directly (a confirmation box) or shows you the
preview and waits for your go-ahead. Once applied, the operation can be undone:

> **You:** Undo that.

See [Safety by design](../concepts/safety.md) for how confirmation and undo work.

## 5. Use the ready-made workflows

Avenir ships prompts your client can offer as commands:

| Prompt | What it walks you through |
|---|---|
| `classify_pending` | suggestions, your choices, one confirmed batch, the undo id |
| `monthly_review` | totals, what stands out, proposed fixes |
| `reconcile` | the gap with your bank explained, then a confirmed reconciliation |
| `plan_next_month` | a forecast and its assumptions, then next month's amounts |

In Claude Code they appear among the slash commands of the `avenir` server.
