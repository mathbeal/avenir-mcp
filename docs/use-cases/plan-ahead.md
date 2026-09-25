# Plan ahead

**Goal:** know whether the money lasts, and prepare next month's budget.

## Ask

> If I earn 3,200 a month, will my accounts go below zero before the end of the year?

or run the `plan_next_month` prompt.

## What happens

**`forecast_balance`** projects the balance month by month, up to 24 months ahead,
and returns the assumptions it used, so you can correct them:

```json
--8<-- "snippets/forecast.json"
```

- **Recurring charges** come from your history: the same payee in 3 of the last 4
  months, at a stable amount (rent, phone, subscriptions). They fall on their usual
  day.
- **Other spending** is the average of the last 3 months, spread over the days.
- **Income** is what you give (`monthly_income`), which replaces what the history
  shows; without it, the history's average.
- **One-off amounts** — a yearly tax, a refund — are yours to add.
- For the current month, what was already spent or received is deducted, so only
  what is left is projected.

`lowest` is the lowest point within each month; `first_shortfall` names the first
month it goes below zero.

!!! warning "A projection, not a prediction"
    It extrapolates your recent months. Read the assumptions before the conclusion,
    and add what you know is coming.

## Then budget next month

With the forecast in mind, Claude proposes next month's amounts category by
category and applies the ones you accept with `set_category_budget`.
