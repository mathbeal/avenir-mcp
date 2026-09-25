# Avenir — an MCP server for YNAB

[![quality](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml)
[![docs](https://github.com/mathbeal/avenir-mcp/actions/workflows/docs.yml/badge.svg)](https://mathbeal.github.io/avenir-mcp/)
[![python](https://img.shields.io/badge/python-3.14-blue)](https://github.com/mathbeal/avenir-mcp)
[![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/mathbeal/avenir-mcp)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/mathbeal/avenir-mcp/blob/main/LICENSE)

> 🇬🇧 **Avenir** (French for *the future*) lets an AI agent read your YNAB budget
> and help you plan what comes next.
>
> 🇫🇷 **Avenir** permet à un agent IA de lire votre budget YNAB et de vous aider
> à préparer la suite.

Ask Claude — or any [MCP](https://modelcontextprotocol.io) client — about your budget
in plain words: where the money went, what still needs a category, whether an account
matches the bank, when money would run out. Every change is previewed, confirmed by
you, and can be undone.

**📖 Documentation: <https://mathbeal.github.io/avenir-mcp/>**

> **Not affiliated with or endorsed by YNAB.** YNAB and You Need A Budget are
> registered trademarks of YNAB.

## Why Avenir

- **Tools for tasks, not endpoints.** Classify a month of transactions, reconcile an
  account, forecast your balance: one tool each, not a wrapper of YNAB's API.
- **Read-only by default.** Tools that change your budget exist only when you enable
  them.
- **Preview, confirm, undo.** Every write shows what will change and waits for your
  yes; `undo_operation` reverts it.
- **Answers an agent can read.** Currency units, short typed answers, pagination,
  errors that say what to fix, bank text treated as untrusted.
- **Verified.** 100 % line and branch coverage, and an evaluation where a real agent
  works on an invented budget: 9/9 tasks.

## Install

You need [uv](https://docs.astral.sh/uv/) and a YNAB personal access token
(YNAB → Account Settings → Developer Settings → New Token).

```bash
# Claude Code
claude mcp add avenir --env YNAB_API_KEY=your-token --env AVENIR_MCP_WRITE=1 -- uvx avenir-mcp
```

```jsonc
// Claude Desktop, Cursor: the mcpServers block of the client's configuration
{
  "mcpServers": {
    "avenir": {
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

| You ask | Avenir |
|---|---|
| "Which category is overspent this month?" | `get_monthly_summary` — totals and overspent categories |
| "Categorise what is pending." | `suggest_categories`, then `apply_categories` after your yes |
| "My bank shows 3,440.80. Does YNAB agree?" | `reconcile_account` — explains the gap, changes nothing until it matches |
| "Will I go below zero before December?" | `forecast_balance` — month by month, with its assumptions |
| "Move 30 from Leisure to Restaurants." | `set_category_budget`, previewed and undoable |
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
