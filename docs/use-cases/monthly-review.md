# Review a month

**Goal:** understand where the money went and fix what went off track.

## Ask

> Review September with me.

or run the `monthly_review` prompt.

## What happens

1. **`get_monthly_summary`** gives the month at a glance — income, budgeted, spent,
   Ready to Assign — and only the categories that are overspent:

    ```json
    --8<-- "snippets/monthly_summary.json"
    ```

2. **`get_category_balances`** and **`get_spending_trends`** explain what stands
   out: is Restaurants high this month, or every month?

    ```json
    --8<-- "snippets/category_balances.json"
    ```

3. Claude proposes fixes — usually moving money from a category with room to the
   overspent one — and applies them with `set_category_budget` once you agree:

    ```json
    --8<-- "snippets/budget_preview.json"
    ```

## Tips

- Overspending is fixed by moving money between categories, not by ignoring it:
  that is the YNAB method, and the `avenir://guide` resource reminds agents of it.
- Categories with nothing budgeted, spent or available are left out of
  `get_category_balances` unless you ask for `include_empty`.
