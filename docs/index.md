---
hide:
  - navigation
---

# Avenir

**An MCP server for [YNAB](https://www.ynab.com), built for agents.**
Ask Claude — or any MCP client — about your budget in plain words: where the money
went, what still needs a category, whether your account matches the bank, when money
would run out. Every change is previewed, confirmed by you, and can be undone.

*Avenir* is French for *the future*.

!!! warning "Not affiliated with YNAB"
    YNAB and You Need A Budget are registered trademarks of YNAB. Avenir is an
    independent project that uses YNAB's public API with your own access token.

<div class="grid cards" markdown>

-   :material-shield-check:{ .lg .middle } **Read-only by default**

    ---

    Tools that change your budget do not even exist until you enable them.
    [Safety by design](concepts/safety.md)

-   :material-eye-check:{ .lg .middle } **Preview, confirm, undo**

    ---

    Every write shows what will change and waits for your yes. One call reverts it.

-   :material-robot-outline:{ .lg .middle } **Tools for tasks, not endpoints**

    ---

    Classify a month of transactions, reconcile an account, forecast your balance:
    one tool each. [Use cases](use-cases/classify.md)

-   :material-chart-line:{ .lg .middle } **Answers an agent can read**

    ---

    Amounts in currency units, short typed answers, pagination, actionable errors.

</div>

## A taste

> **You:** Which category is overspent in September, and by how much?

Claude calls `get_monthly_summary`, which answers in a few lines:

```json
--8<-- "snippets/monthly_summary.json"
```

> **Claude:** Restaurants is overspent by 22.50 in September: 120 was budgeted and
> 142.50 spent. Want me to move 30 from Leisure to cover it?

The examples in this documentation are real answers from Avenir, run on an invented
demo budget: no real account appears anywhere.

## Next

- [Install Avenir](getting-started/install.md) in Claude Code, Claude Desktop, Cursor or VS Code.
- [Have a first conversation](getting-started/first-conversation.md).
- Browse the [tools, resources and prompts](reference/tools.md).
