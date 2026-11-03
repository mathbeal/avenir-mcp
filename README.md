# avenir-mcp: an unofficial MCP server for YNAB

<!-- mcp-name: io.github.mathbeal/avenir-mcp -->

**avenir-mcp** (*avenir* is French for *the future*) lets an AI agent read your YNAB plan
and help you plan what comes next.

[English](https://avenir-mcp.pages.dev/avenir-mcp/) · [Français](https://avenir-mcp.pages.dev/avenir-mcp/fr/) · [Español](https://avenir-mcp.pages.dev/avenir-mcp/es/) · [Deutsch](https://avenir-mcp.pages.dev/avenir-mcp/de/) · [Nederlands](https://avenir-mcp.pages.dev/avenir-mcp/nl/)

[![Works with YNAB](https://api.ynab.com/papi/works_with_ynab.svg)](https://api.ynab.com/#works-with-ynab-third-party)
[![PyPI](https://img.shields.io/pypi/v/avenir-mcp)](https://pypi.org/project/avenir-mcp/)
[![python](https://img.shields.io/pypi/pyversions/avenir-mcp)](https://pypi.org/project/avenir-mcp/)
[![quality](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15139/badge)](https://www.bestpractices.dev/projects/15139)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/mathbeal/avenir-mcp/blob/main/LICENSE)

Ask Claude, or any [MCP](https://modelcontextprotocol.io) client, about your plan in
plain words. Read-only by default; every change is previewed, confirmed by you, and can
be undone.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/demo-dark.svg">
  <img alt="One conversation, in thirty seconds. Asked how the month is going and where the room is, the agent calls four read-only tools at the same time: Month summary, Every category, Budget vs spent and Three months. It answers that Restaurants is the only category over budget: 166.50 spent of 144.00 available (120.00 budgeted + 24.00 left from earlier months), 138.8 %, available −22.50; that its spending rose 113.70 → 119.90 → 166.50 over three months; and that 80.00 is left in Tennis and 411.90 in Groceries. It offers to cover the 22.50 from Tennis, which has nothing spent yet. The user answers “Cover it from Tennis.”, and move_money shows a preview that changes nothing: Tennis budgeted 80.00 → 57.50, Restaurants budgeted 120.00 → 142.50, available −22.50 → 0.00, exactly on budget, with a Cancel button, a Confirm button, and the reminder that nothing changes until you confirm and that any change can be undone." src="https://raw.githubusercontent.com/mathbeal/avenir-mcp/main/.github/assets/demo-light.svg" width="720">
</picture>

▶ [Watch the 20-second tour](https://avenir-mcp.pages.dev/avenir-mcp/#tour)

This comes from an invented demo plan, replayed by `python -m docsgen`: every figure is
what avenir-mcp answers today.

## What you can ask

- **Understand a month:** "Which category is overspent this month?" → `get_monthly_summary`
- **Prepare a spend:** "Will I go below zero before December?" → `forecast_balance`
- **Pay off a debt:** "When will my debts be paid off if I put 500 a month on them?" → `get_debt_payoff_plan`
- **Tidy the transactions:** "Categorise what is pending." → `suggest_categories`, applied after your yes
- **Find one transaction:** "Which transaction is my 86.40 receipt from the 12th?" → `find_transactions`
- **Reconcile an account:** "My bank shows 3,440.80. Does YNAB agree?" → `reconcile_account`
- **Change something:** "Move 30 from Tennis to Restaurants." → `move_money`, previewed, confirmed, and undone by `undo_operation`

Every tool, with a real answer:
[Reference](https://avenir-mcp.pages.dev/avenir-mcp/reference/tools/) ·
[Use cases](https://avenir-mcp.pages.dev/avenir-mcp/guides/classify/).

## More than an API wrapper

YNAB's API gives data; these tools give answers computed from it, with every write
confirmed first:

- **`forecast_balance`** projects the balance forward month by month, from scheduled
  transactions, recent spending and what you give it.
- **`get_runway`** says how many months the money in the budget would last without
  income.
- **`get_debt_payoff_plan`** pays debts down month by month, avalanche or snowball, and
  says when each is paid off.
- **`find_recurring_charges`** finds what is paid most months, ranked by its yearly
  cost, so a subscription does not go unnoticed.
- **`suggest_categories`** proposes a category for a pending transaction from how its
  payee was categorised before.
- Every write is previewed first; the confirmation is bound to that exact preview, and
  `undo_operation` reverts it.

## Install

You need a YNAB personal access token: YNAB → Account Settings → Developer Settings →
New Token.

[![Download for Claude Desktop](https://img.shields.io/badge/Claude_Desktop-Download_the_extension-D97757?style=flat-square&logo=claude&logoColor=white)](https://github.com/mathbeal/avenir-mcp/releases/latest/download/avenir-mcp.mcpb)

**Claude Desktop**, no terminal: drop the file the button downloads onto **Settings →
Extensions**, then paste your token on that screen.

**Claude Code**, one command with your token in it:

```bash
claude mcp add avenir-mcp --env YNAB_API_KEY=your-token -- uvx avenir-mcp
```

Both install it read-only. Cursor, LM Studio, VS Code, Windows, changes to your plan
(`AVENIR_MCP_WRITE=1`) and every option:
[Install](https://avenir-mcp.pages.dev/avenir-mcp/getting-started/install/) ·
[Configuration](https://avenir-mcp.pages.dev/avenir-mcp/reference/configuration/).

### With a local model

A model running on your own machine, for instance through [LM Studio](https://lmstudio.ai),
keeps your transactions off any AI provider's servers: see [Where your data
goes](https://avenir-mcp.pages.dev/avenir-mcp/guides/choose-a-model/#where-your-data-goes).
Small local models call tools less reliably than the current large cloud models: in the
[evaluation](https://avenir-mcp.pages.dev/avenir-mcp/project/evaluation/#local-models), a
7B model served locally passed only 1 of 25 tasks, getting every write wrong. With a
local model, keep avenir-mcp read-only (no `AVENIR_MCP_WRITE`), or set
`AVENIR_MCP_REQUIRE_ELICITATION=1` so that only your own answer in the client, never a
model relaying a confirmation code on its own, can confirm a change.

## Why avenir-mcp

- **Tools for tasks, not endpoints.** One tool classifies a month, one reconciles an account.
- **Read-only by default.** The tools that change a plan are registered only if you enable them.
- **Preview, confirm, undo.** A write waits for your yes; `undo_operation` reverts it.
- **Answers an agent can read.** Currency units, typed answers, bank text treated as untrusted.
- **Verified.** 100 % line and branch coverage, and a real agent on an invented plan: 25/25.

**📖 Documentation:** <https://avenir-mcp.pages.dev/avenir-mcp/>

**Missing a question? Have an idea?** Tell us the question you would like to ask your budget
in [Discussions → Ideas](https://github.com/mathbeal/avenir-mcp/discussions/categories/ideas);
help with using avenir-mcp is in
[Discussions → Q&A](https://github.com/mathbeal/avenir-mcp/discussions/categories/q-a).
Never post a real amount, a real account or your token.

## Claude Code plugin

`plugin/` is avenir-mcp as a Claude Code plugin: Claude Code asks for your token, keeps it
out of sight, and starts the server from the plugin's own locked environment. From a clone:
`claude --plugin-dir plugin`.

| The plugin | What |
|---|---|
| runs | `uv run --locked --project` *the plugin's folder*, which starts the release `plugin/pyproject.toml` pins, and nothing else. No script of its own, no build step, no hook, no shell |
| contacts | `pypi.org` and `files.pythonhosted.org`, to install that release and the versions `plugin/uv.lock` pins, the first time; then `api.ynab.com`, with your token, as avenir-mcp always does |
| writes | the environment `uv` resolves inside the plugin's folder, and `uv`'s own cache. Nothing elsewhere |
| changes in your plan | nothing. It starts avenir-mcp read-only: `AVENIR_MCP_WRITE` is not set, so the tools that change a plan are never registered |

## Development

```bash
git clone https://github.com/mathbeal/avenir-mcp && cd avenir-mcp
uv sync
just check        # lint, types, tests at 100 % coverage, vocabulary, lockfile
just docs-serve   # the documentation, live
just evaluate     # a real agent on the demo plan (uses your Claude plan)
```

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull
request. Security reports: [SECURITY.md](SECURITY.md). Also: [ARCHITECTURE.md](ARCHITECTURE.md),
[ROADMAP.md](ROADMAP.md), [GOVERNANCE.md](GOVERNANCE.md) and the
[code of conduct](CODE_OF_CONDUCT.md).

Built and tested against YNAB's API v1.88.0; a weekly
[`YNAB API drift`](https://github.com/mathbeal/avenir-mcp/actions/workflows/api-drift.yml)
check fails when YNAB publishes a new version. Self-checked on every change against
YNAB's API terms of 2025-05-28 (naming, attribution, YNAB's own image, a personal token
for its owner only, the hourly limit); a weekly job turns that badge red when they change:
[![YNAB API terms: self-checked](https://github.com/mathbeal/avenir-mcp/actions/workflows/ynab-terms.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/ynab-terms.yml)

## Privacy Policy

avenir-mcp is a program you run yourself, not a service: its publisher runs no server and
receives none of your data. Your token is read from the environment, kept in memory as a
secret value and sent only to YNAB; your plan's data is fetched when a tool needs it and
returned to your agent, so the model provider behind your MCP client sees it too. What is
handled, how long it is kept and how to erase it:
<https://avenir-mcp.pages.dev/avenir-mcp/project/privacy/>.

## Licence

MIT.

## Unofficial project

We are not affiliated, associated, or in any way officially connected with YNAB or any of
its subsidiaries or affiliates. The official YNAB website can be found at
https://www.ynab.com. The names YNAB and You Need A Budget, as well as related names,
tradenames, marks, trademarks, emblems, and images are registered trademarks of YNAB. They
are named here only to say which service avenir-mcp works with. Listed by YNAB in its
[Works with YNAB](https://api.ynab.com/#works-with-ynab-third-party) directory, among
third-party apps. Not endorsed by YNAB.

avenir-mcp is for **personal use on your own machine, with your own YNAB token**. Running
it as a public or shared server is not supported. It is provided as is, without warranty,
and is not financial advice: you remain responsible for the changes you confirm. See the
[legal notice](https://avenir-mcp.pages.dev/avenir-mcp/project/legal/).
