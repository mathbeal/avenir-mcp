# Organise categories

**Goal:** keep the category structure tidy as your life changes.

| Ask | Tool |
|---|---|
| "Create a *Pets* category in Everyday." | `create_category` |
| "Rename *Gym* to *Sport*." | `update_category` |
| "Move *Books* from Fun to Education." | `update_category` |
| "Put 150 in Restaurants for September." | `set_category_budget` |

Each one previews the change and waits for your confirmation. A name already used in
the group is refused.

```json
--8<-- "snippets/budget_preview.json"
```

!!! note "Deleting a category"
    YNAB's API cannot delete a category. To undo a creation, hide the category in
    YNAB.
