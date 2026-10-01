# avenir-mcp — an unofficial MCP server for YNAB

<!-- mcp-name: io.github.mathbeal/avenir-mcp -->

[![Works with YNAB](https://api.ynab.com/papi/works_with_ynab.svg)](https://api.ynab.com/)
[![YNAB API terms: self-checked](https://github.com/mathbeal/avenir-mcp/actions/workflows/ynab-terms.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/ynab-terms.yml)

Self-checked on every change against YNAB's API terms of 2025-05-28 (naming, attribution,
YNAB's own image, a personal token for its owner only, the hourly limit); a weekly job
turns the badge red when YNAB changes its terms. Not reviewed or endorsed by YNAB.

[![quality](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml)
[![MCP Inspector](https://github.com/mathbeal/avenir-mcp/actions/workflows/inspector.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/inspector.yml)
[![docs](https://github.com/mathbeal/avenir-mcp/actions/workflows/docs.yml/badge.svg)](https://mathbeal.github.io/avenir-mcp/)

[![PyPI](https://img.shields.io/pypi/v/avenir-mcp)](https://pypi.org/project/avenir-mcp/)
[![python](https://img.shields.io/pypi/pyversions/avenir-mcp)](https://pypi.org/project/avenir-mcp/)
[![coverage](https://img.shields.io/badge/coverage-100%25%20lines%20and%20branches-brightgreen)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![types](https://img.shields.io/badge/types-mypy%20strict-blue)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![docstrings](https://img.shields.io/badge/docstrings-Google%20style%2C%20ruff-blue)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![code style](https://img.shields.io/badge/code%20style-ruff-261230)](https://mathbeal.github.io/avenir-mcp/project/development/#the-checks)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/mathbeal/avenir-mcp/blob/main/LICENSE)
[![last commit](https://img.shields.io/github/last-commit/mathbeal/avenir-mcp)](https://github.com/mathbeal/avenir-mcp/commits/main)

> 🇬🇧 **avenir-mcp** (*avenir* is French for *the future*) lets an AI agent read your YNAB plan
> and help you plan what comes next.
>
> 🇫🇷 **avenir-mcp** permet à un agent IA de lire votre plan YNAB et de vous aider
> à préparer la suite.

Ask Claude — or any [MCP](https://modelcontextprotocol.io) client — about your plan
in plain words: where the money went, what still needs a category, whether an account
matches the bank, when money would run out. Every change is previewed, confirmed by
you, and can be undone.

**📖 Documentation: <https://mathbeal.github.io/avenir-mcp/>**

[English](https://mathbeal.github.io/avenir-mcp/) · [Français](https://mathbeal.github.io/avenir-mcp/fr/) · [Español](https://mathbeal.github.io/avenir-mcp/es/) · [Deutsch](https://mathbeal.github.io/avenir-mcp/de/) · [Nederlands](https://mathbeal.github.io/avenir-mcp/nl/)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/conversation-dark.svg">
  <img alt="Asked how the September budget is doing, the agent reads the month with two read-only tools and answers: one category over budget, Restaurants by 22.50, everything else on track." src="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/conversation-light.svg" width="720">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/forecast-dark.svg">
  <img alt="forecast_balance on the demo plan: the month-end balance rises from September to December, with each month's lowest day and a yearly insurance payment scheduled on 20 October." src="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/forecast-light.svg" width="720">
</picture>

Both come from the invented demo plan: a real reply of Claude Sonnet, and the forecast
the documentation shows.

> **Unofficial project.** We are not affiliated, associated, or in any way officially
> connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website
> can be found at https://www.ynab.com. The names YNAB and You Need A Budget, as well as
> related names, tradenames, marks, trademarks, emblems, and images are registered
> trademarks of YNAB. They are named here only to say which service avenir-mcp works with.
>
> avenir-mcp is for **personal use on your own machine, with your own YNAB token**. Running it
> as a public or shared server is not supported. It is provided as is, without warranty,
> and is not financial advice: you remain responsible for the changes you confirm. See the
> [legal notice](https://mathbeal.github.io/avenir-mcp/project/legal/).

## Why avenir-mcp

- **Tools for tasks, not endpoints.** Classify a month of transactions, reconcile an
  account, forecast your balance: one tool each, not a wrapper of YNAB's API.
- **Read-only by default.** Tools that change your plan exist only when you enable
  them.
- **Preview, confirm, undo.** Every write shows what will change and waits for your
  yes; `undo_operation` reverts it.
- **Answers an agent can read.** Currency units, short typed answers, pagination,
  errors that say what to fix, bank text treated as untrusted.
- **Verified.** 100 % line and branch coverage, and an evaluation where a real agent
  works on an invented plan: 19/19 tasks.

## Install

You need [uv](https://docs.astral.sh/uv/) and a YNAB personal access token
(YNAB → Account Settings → Developer Settings → New Token).

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_avenir--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=avenir-mcp&inputs=%5B%7B%22id%22%3A%22ynab_token%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22YNAB%20personal%20access%20token%22%2C%22password%22%3Atrue%7D%5D&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22avenir-mcp%22%5D%2C%22env%22%3A%7B%22YNAB_API_KEY%22%3A%22%24%7Binput%3Aynab_token%7D%22%7D%7D)
[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=avenir-mcp&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJhdmVuaXItbWNwIl0sImVudiI6eyJZTkFCX0FQSV9LRVkiOiJ5b3VyLXRva2VuIn19)

One click installs avenir-mcp **read-only**: VS Code asks for your token in a password box and keeps it in its secret
storage; in Cursor, replace `your-token` in the server's settings. Add `AVENIR_MCP_WRITE=1` to allow changes.

Or by hand:

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

Walk-throughs with real answers: [Use cases](https://mathbeal.github.io/avenir-mcp/guides/classify/).
Every tool, resource and prompt: [Reference](https://mathbeal.github.io/avenir-mcp/reference/tools/).

## Development

```bash
git clone https://github.com/mathbeal/avenir-mcp && cd avenir-mcp
uv sync
just check        # lint, types, tests at 100 % coverage, vocabulary, lockfile
just docs-serve   # the documentation, live
just evaluate     # a real agent on the demo plan (uses your Claude plan)
```

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a
pull request. Security reports: [SECURITY.md](SECURITY.md). Also:
[ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md),
[GOVERNANCE.md](GOVERNANCE.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## Licence

MIT.
