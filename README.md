# avenir-mcp — an unofficial MCP server for YNAB

[![quality](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml)
[![MCP Inspector](https://github.com/mathbeal/avenir-mcp/actions/workflows/inspector.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/inspector.yml)
[![docs](https://github.com/mathbeal/avenir-mcp/actions/workflows/docs.yml/badge.svg)](https://mathbeal.github.io/avenir-mcp/)

[![python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![coverage](https://img.shields.io/badge/coverage-100%25%20lines%20and%20branches-brightgreen)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![types](https://img.shields.io/badge/types-mypy%20strict-blue)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![docstrings](https://img.shields.io/badge/docstrings-Google%20style%2C%20ruff-blue)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![code style](https://img.shields.io/badge/code%20style-black-000000)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/mathbeal/avenir-mcp/blob/main/LICENSE)

> 🇬🇧 **avenir-mcp** (*avenir* is French for *the future*) lets an AI agent read your YNAB budget
> and help you plan what comes next.
>
> 🇫🇷 **avenir-mcp** permet à un agent IA de lire votre budget YNAB et de vous aider
> à préparer la suite.

Ask Claude — or any [MCP](https://modelcontextprotocol.io) client — about your budget
in plain words: where the money went, what still needs a category, whether an account
matches the bank, when money would run out. Every change is previewed, confirmed by
you, and can be undone.

**📖 Documentation: <https://mathbeal.github.io/avenir-mcp/>**

> **Unofficial project.** We are not affiliated, associated, or in any way officially
> connected with YNAB or any of its subsidiaries or affiliates. YNAB and You Need A Budget
> are registered trademarks of YNAB, named here only to say which service avenir-mcp works
> with.
>
> avenir-mcp is for **personal use on your own machine, with your own YNAB token**. Running it
> as a public or shared server is not supported. It is provided as is, without warranty,
> and is not financial advice: you remain responsible for the changes you confirm. See the
> [legal notice](https://mathbeal.github.io/avenir-mcp/project/legal/).

## Why avenir-mcp

- **Tools for tasks, not endpoints.** Classify a month of transactions, reconcile an
  account, forecast your balance: one tool each, not a wrapper of YNAB's API.
- **Read-only by default.** Tools that change your budget exist only when you enable
  them.
- **Preview, confirm, undo.** Every write shows what will change and waits for your
  yes; `undo_operation` reverts it.
- **Answers an agent can read.** Currency units, short typed answers, pagination,
  errors that say what to fix, bank text treated as untrusted.
- **Verified.** 100 % line and branch coverage, and an evaluation where a real agent
  works on an invented budget: 11/11 tasks.

## Install

You need [uv](https://docs.astral.sh/uv/) and a YNAB personal access token
(YNAB → Account Settings → Developer Settings → New Token).

```bash
# Claude Code
claude mcp add avenir-mcp --env YNAB_API_KEY=your-token --env AVENIR_MCP_WRITE=1 -- uvx avenir-mcp
```

```jsonc
// Claude Desktop, Cursor: the mcpServers block of the client's configuration
{
  "mcpServers": {
    "avenir-mcp": {
      "command": "uvx",
      "args": ["avenir-mcp"],
      "env": { "YNAB_API_KEY": "your-token", "AVENIR_MCP_WRITE": "1" }
    }
  }
}
```

Drop `AVENIR_MCP_WRITE` to stay read-only. Other clients and every option:
[Install](https://mathbeal.github.io/avenir-mcp/getting-started/install/) ·
[Configuration](https://mathbeal.github.io/avenir-mcp/reference/configuration/).

## What you can ask

| You ask | avenir-mcp |
|---|---|
| "Which category is overspent this month?" | `get_monthly_summary` — totals and overspent categories |
| "Categorise what is pending." | `suggest_categories`, then `apply_categories` after your yes |
| "Split this receipt: 81.15 groceries, 5.25 household." | `split_transaction` — one transaction across categories, after your yes |
| "Which transaction is my 86.40 receipt from the 12th?" | `find_transactions` — by dates, exact amount and account, categorised or not |
| "My bank shows 3,440.80. Does YNAB agree?" | `reconcile_account` — explains the gap, changes nothing until it matches |
| "Will I go below zero before December?" | `forecast_balance` — month by month, with its assumptions |
| "Move 30 from Tennis to Restaurants." | `set_category_budget`, previewed and undoable |
| "Undo that." | `undo_operation` |

Walk-throughs with real answers: [Use cases](https://mathbeal.github.io/avenir-mcp/use-cases/classify/).
Every tool, resource and prompt: [Reference](https://mathbeal.github.io/avenir-mcp/reference/tools/).

## Development

```bash
git clone https://github.com/mathbeal/avenir-mcp && cd avenir-mcp
uv sync
just check        # lint, types, tests at 100 % coverage, vocabulary, lockfile
just docs-serve   # the documentation, live
just evaluate     # a real agent on the demo budget (uses your Claude plan)
```

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a
pull request. Security reports: [SECURITY.md](SECURITY.md).

## Licence

MIT.
